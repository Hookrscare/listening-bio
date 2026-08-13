#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="/opt/listening-bio"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.production.yml"
ENV_FILE="$PROJECT_DIR/.env.production"
HERMES_REPORT_DIR="/docker/hermes-agent-vliu/data/listening-bio"
BACKUP_DIR="/var/backups/listening-bio"
AUDIT_LOG="/var/log/listening-bio-operator.log"
LOCK_FILE="/run/lock/listening-bio-operator.lock"

mkdir -p "$HERMES_REPORT_DIR" "$BACKUP_DIR"
chmod 750 "$HERMES_REPORT_DIR" "$BACKUP_DIR"
exec 9>"$LOCK_FILE"
flock -n 9 || exit 0

compose() {
  docker compose --project-directory "$PROJECT_DIR" \
    -f "$COMPOSE_FILE" --env-file "$ENV_FILE" "$@"
}

audit() {
  printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >> "$AUDIT_LOG"
}

container_state() {
  local service="$1"
  compose ps --format json "$service" 2>/dev/null \
    | jq -r 'if type == "array" then (.[0].State // "missing") else (.State // "missing") end' \
    | head -n 1
}

health_check() {
  curl --fail --silent --show-error --max-time 10 \
    https://api.listening.bio/health >/dev/null
}

heal_service() {
  local service="$1"
  audit "recovery requested service=$service"
  compose up -d --no-deps "$service" >> "$AUDIT_LOG" 2>&1
}

write_report() {
  local api_state postgres_state worker_state disk_used cert_status status latest_backup
  api_state="$(container_state api)"
  postgres_state="$(container_state postgres)"
  worker_state="$(container_state worker)"
  disk_used="$(df --output=pcent / | tail -1 | tr -d ' ')"
  cert_status="$(openssl s_client -connect api.listening.bio:443 -servername api.listening.bio </dev/null 2>/dev/null \
    | openssl x509 -noout -checkend 1209600 >/dev/null 2>&1 && echo 'valid for more than 14 days' || echo 'expires within 14 days')"
  latest_backup="$(find "$BACKUP_DIR" -maxdepth 1 -name '*.sql.gz' -printf '%f\n' 2>/dev/null | sort | tail -1)"
  latest_backup="${latest_backup:-none}"

  status="healthy"
  health_check || status="attention"
  [[ "$api_state" == "running" && "$postgres_state" == "running" && "$worker_state" == "running" ]] || status="attention"

  cat > "$HERMES_REPORT_DIR/status.md.tmp" <<EOF
# Listening.bio operator status

- Overall: $status
- Checked: $(date --iso-8601=seconds)
- Public API: https://api.listening.bio/health
- API container: $api_state
- PostgreSQL/PostGIS: $postgres_state
- Worker: $worker_state
- Root disk used: $disk_used
- TLS certificate: $cert_status
- Latest backup: $latest_backup

Hermes may summarize this report. Infrastructure changes, deployments, DNS changes,
database restores, and data deletion still require Rodrigo's explicit approval.
EOF
  mv "$HERMES_REPORT_DIR/status.md.tmp" "$HERMES_REPORT_DIR/status.md"
  chmod 640 "$HERMES_REPORT_DIR/status.md"
}

check_and_heal() {
  if ! health_check; then
    audit "public health check failed"
    heal_service api
    sleep 10
  fi

  [[ "$(container_state worker)" == "running" ]] || heal_service worker
  [[ "$(container_state postgres)" == "running" ]] || audit "postgres is not running; automatic restart withheld"
  write_report
}

backup_database() {
  local timestamp target
  timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
  target="$BACKUP_DIR/listening-bio-$timestamp.sql.gz"
  compose exec -T postgres pg_dump -U listening_bio -d listening_bio \
    | gzip -9 > "$target.tmp"
  gzip -t "$target.tmp"
  mv "$target.tmp" "$target"
  chmod 600 "$target"
  audit "database backup completed file=$(basename "$target")"
  write_report
}

case "${1:-check}" in
  check) check_and_heal ;;
  status) write_report ;;
  backup) backup_database ;;
  *) echo "Usage: $0 {check|status|backup}" >&2; exit 2 ;;
esac
