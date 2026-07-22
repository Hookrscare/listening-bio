import type { DemoDetection, DemoProvenance, ReviewStatus } from "../data/demoData";

function downloadBlob(filename: string, contents: string, type: string) {
  const blob = new Blob([contents], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function csvCell(value: string | number | boolean): string {
  const s = String(value);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

export interface ExportRow {
  detection: DemoDetection;
  reviewStatus: ReviewStatus;
}

const HEADERS = [
  "detection_id",
  "label",
  "scientific_name",
  "detection_type",
  "confidence",
  "start_seconds",
  "end_seconds",
  "frequency_min_hz",
  "frequency_max_hz",
  "review_status",
  "recording_id",
  "model_name",
  "model_version",
  "evidence_level",
  "demonstration_only",
] as const;

export function buildDetectionsCsv(
  rows: ExportRow[],
  prov: DemoProvenance,
): string {
  const lines = [HEADERS.join(",")];
  for (const { detection: d, reviewStatus } of rows) {
    lines.push(
      [
        d.id,
        d.label,
        d.scientificName ?? "",
        d.detectionType,
        d.confidence,
        d.startSeconds,
        d.endSeconds,
        d.frequencyMinHz,
        d.frequencyMaxHz,
        reviewStatus,
        prov.recordingId,
        prov.modelName,
        prov.modelVersion,
        prov.evidenceLevel,
        "true",
      ]
        .map(csvCell)
        .join(","),
    );
  }
  return lines.join("\n");
}

export function buildDetectionsGeoJson(
  rows: ExportRow[],
  prov: DemoProvenance,
): string {
  const features = rows.map(({ detection: d, reviewStatus }) => ({
    type: "Feature" as const,
    geometry: {
      type: "Point" as const,
      coordinates: [prov.longitude, prov.latitude],
    },
    properties: {
      detection_id: d.id,
      label: d.label,
      scientific_name: d.scientificName ?? null,
      confidence: d.confidence,
      start_seconds: d.startSeconds,
      end_seconds: d.endSeconds,
      frequency_min_hz: d.frequencyMinHz,
      frequency_max_hz: d.frequencyMaxHz,
      review_status: reviewStatus,
      recording_id: prov.recordingId,
      evidence_level: prov.evidenceLevel,
      demonstrationOnly: true,
      claim_status: "Representative demonstration data — not a scientific finding",
    },
  }));
  return JSON.stringify(
    { type: "FeatureCollection", features },
    null,
    2,
  );
}

export function exportDetectionsCsv(rows: ExportRow[], prov: DemoProvenance) {
  downloadBlob(
    "listening-bio-demo-detections.csv",
    buildDetectionsCsv(rows, prov),
    "text/csv;charset=utf-8",
  );
}

export function exportDetectionsGeoJson(rows: ExportRow[], prov: DemoProvenance) {
  downloadBlob(
    "listening-bio-demo-detections.geojson",
    buildDetectionsGeoJson(rows, prov),
    "application/geo+json",
  );
}
