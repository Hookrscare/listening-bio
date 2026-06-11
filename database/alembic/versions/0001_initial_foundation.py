"""initial foundation

Revision ID: 0001_initial_foundation
Revises:
Create Date: 2026-06-10
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_foundation"
down_revision = None
branch_labels = None
depends_on = None


def _id_column() -> sa.Column:
    return sa.Column("id", sa.String(length=36), primary_key=True)


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "organizations",
        _id_column(),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("external_id", sa.String(120), unique=True),
        sa.Column("organization_type", sa.String(80)),
        sa.Column("website_url", sa.String(500)),
        *_timestamps(),
    )
    op.create_table(
        "users",
        _id_column(),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        *_timestamps(),
    )
    op.create_table(
        "memberships",
        _id_column(),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_membership_org_user"),
    )
    op.create_table(
        "projects",
        _id_column(),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("external_id", sa.String(120), unique=True),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(50), nullable=False),
        *_timestamps(),
    )
    op.create_table(
        "sites",
        _id_column(),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("external_id", sa.String(120), unique=True),
        sa.Column("habitat_type", sa.String(120)),
        sa.Column("latitude", sa.Float),
        sa.Column("longitude", sa.Float),
        sa.Column("location_geom_wkt", sa.Text),
        *_timestamps(),
    )
    op.create_table(
        "audio_files",
        _id_column(),
        sa.Column("site_id", sa.String(36), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("uploaded_by_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("idempotency_key", sa.String(120)),
        sa.Column("storage_uri", sa.String(800), nullable=False),
        sa.Column("content_type", sa.String(120), nullable=False),
        sa.Column("duration_seconds", sa.Float),
        sa.Column("recorded_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(50), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("status in ('uploaded', 'queued', 'processing', 'processed', 'failed')", name="ck_audio_file_status"),
        sa.UniqueConstraint("site_id", "idempotency_key", name="uq_audio_file_site_idempotency_key"),
    )
    op.create_table(
        "processing_jobs",
        _id_column(),
        sa.Column("audio_file_id", sa.String(36), sa.ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("job_type", sa.String(80), nullable=False),
        sa.Column("error_message", sa.Text),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        *_timestamps(),
        sa.CheckConstraint("status in ('queued', 'running', 'completed', 'failed', 'cancelled')", name="ck_processing_job_status"),
    )
    op.create_table(
        "ai_models",
        _id_column(),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("version", sa.String(80), nullable=False),
        sa.Column("model_type", sa.String(80), nullable=False),
        sa.Column("provider", sa.String(120)),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("name", "version", name="uq_ai_model_name_version"),
    )
    op.create_table(
        "species_reference",
        _id_column(),
        sa.Column("scientific_name", sa.String(255), nullable=False, unique=True),
        sa.Column("common_name", sa.String(255)),
        sa.Column("gbif_taxon_key", sa.Integer),
        sa.Column("taxon_rank", sa.String(80)),
        *_timestamps(),
    )
    op.create_table(
        "sound_classes",
        _id_column(),
        sa.Column("label", sa.String(255), nullable=False, unique=True),
        sa.Column("source", sa.String(120), nullable=False),
        sa.Column("description", sa.Text),
        *_timestamps(),
    )
    op.create_table(
        "detections",
        _id_column(),
        sa.Column("processing_job_id", sa.String(36), sa.ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("audio_file_id", sa.String(36), sa.ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ai_model_id", sa.String(36), sa.ForeignKey("ai_models.id", ondelete="SET NULL")),
        sa.Column("species_reference_id", sa.String(36), sa.ForeignKey("species_reference.id", ondelete="SET NULL")),
        sa.Column("sound_class_id", sa.String(36), sa.ForeignKey("sound_classes.id", ondelete="SET NULL")),
        sa.Column("detection_type", sa.String(50), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("start_seconds", sa.Float, nullable=False),
        sa.Column("end_seconds", sa.Float, nullable=False),
        sa.Column("review_status", sa.String(50), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("detection_type in ('species', 'sound_class')", name="ck_detection_type"),
        sa.CheckConstraint("review_status in ('unreviewed', 'confirmed', 'rejected')", name="ck_detection_review_status"),
    )
    op.create_table(
        "raw_model_outputs",
        _id_column(),
        sa.Column("processing_job_id", sa.String(36), sa.ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("audio_file_id", sa.String(36), sa.ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ai_model_id", sa.String(36), sa.ForeignKey("ai_models.id", ondelete="SET NULL")),
        sa.Column("output_format", sa.String(80), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        *_timestamps(),
    )
    op.create_table(
        "reports",
        _id_column(),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("report_type", sa.String(80), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("storage_uri", sa.String(800)),
        *_timestamps(),
    )
    op.create_table(
        "grant_opportunities",
        _id_column(),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("funder_name", sa.String(255)),
        sa.Column("deadline", sa.Date),
        sa.Column("status", sa.String(50), nullable=False),
        *_timestamps(),
    )
    op.create_table(
        "grant_tasks",
        _id_column(),
        sa.Column("grant_opportunity_id", sa.String(36), sa.ForeignKey("grant_opportunities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("due_date", sa.Date),
        *_timestamps(),
        sa.CheckConstraint("status in ('todo', 'in_progress', 'done', 'blocked')", name="ck_grant_task_status"),
    )
    op.create_table(
        "partners",
        _id_column(),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("partner_type", sa.String(100)),
        sa.Column("status", sa.String(50), nullable=False),
        *_timestamps(),
    )
    op.create_table(
        "partner_contacts",
        _id_column(),
        sa.Column("partner_id", sa.String(36), sa.ForeignKey("partners.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(255)),
        sa.Column("role_title", sa.String(200)),
        *_timestamps(),
    )
    op.create_table(
        "research_items",
        _id_column(),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("source_url", sa.String(800)),
        sa.Column("notes", sa.Text),
        *_timestamps(),
    )
    op.create_table(
        "outreach_messages",
        _id_column(),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("partner_id", sa.String(36), sa.ForeignKey("partners.id", ondelete="SET NULL")),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        *_timestamps(),
    )
    op.create_table(
        "impact_snapshots",
        _id_column(),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snapshot_date", sa.Date, nullable=False),
        sa.Column("species_richness", sa.Integer, nullable=False),
        sa.Column("biodiversity_activity_score", sa.Float, nullable=False),
        sa.Column("noise_score", sa.Float, nullable=False),
        sa.Column("grant_readiness_score", sa.Float, nullable=False),
        sa.Column("community_value_indicators", sa.JSON, nullable=False),
        sa.Column("metric_label", sa.String(120), nullable=False),
        *_timestamps(),
    )
    op.create_table(
        "weekly_reviews",
        _id_column(),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("week_start_date", sa.Date, nullable=False),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("recommended_actions", sa.JSON, nullable=False),
        *_timestamps(),
    )
    op.create_table(
        "audit_logs",
        _id_column(),
        sa.Column("actor_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("entity_type", sa.String(120), nullable=False),
        sa.Column("entity_id", sa.String(36)),
        sa.Column("metadata_json", sa.JSON, nullable=False),
        *_timestamps(),
    )
    op.create_table(
        "schema_versions",
        _id_column(),
        sa.Column("version", sa.String(80), nullable=False, unique=True),
        sa.Column("source", sa.String(120), nullable=False),
        sa.Column("notes", sa.Text, nullable=False),
        *_timestamps(),
    )


def downgrade() -> None:
    for table_name in [
        "audit_logs",
        "schema_versions",
        "weekly_reviews",
        "impact_snapshots",
        "outreach_messages",
        "research_items",
        "partner_contacts",
        "partners",
        "grant_tasks",
        "grant_opportunities",
        "reports",
        "detections",
        "raw_model_outputs",
        "sound_classes",
        "species_reference",
        "ai_models",
        "processing_jobs",
        "audio_files",
        "sites",
        "projects",
        "memberships",
        "users",
        "organizations",
    ]:
        op.drop_table(table_name)
