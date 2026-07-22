// Typed, privacy-safe analytics stub. No PII, no recording content, no notes,
// no coordinates. Events mirror the spec's suggested list (§18). In production
// this can forward to a consent-safe analytics endpoint; for now it is a no-op
// that keeps a small in-memory buffer for debugging.

export type AnalyticsEvent =
  | "audio_consent_granted"
  | "audio_muted"
  | "sensory_mode_changed"
  | "visual_quality_changed"
  | "hero_pilot_cta_clicked"
  | "evidence_demo_started"
  | "detection_selected"
  | "review_status_changed"
  | "provenance_panel_opened"
  | "export_csv"
  | "export_geojson"
  | "pilot_partner_role_selected"
  | "contact_form_started"
  | "contact_form_submitted";

type AllowedProps = Record<string, string | number | boolean>;

const buffer: Array<{ event: AnalyticsEvent; props?: AllowedProps; ts: number }> =
  [];

export function track(event: AnalyticsEvent, props?: AllowedProps): void {
  buffer.push({ event, props, ts: Date.now() });
  if (import.meta.env.DEV) {
    console.debug("[analytics]", event, props ?? {});
  }
}

export function getAnalyticsBuffer() {
  return [...buffer];
}
