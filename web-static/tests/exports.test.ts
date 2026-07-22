import { describe, expect, it } from "vitest";
import {
  buildDetectionsCsv,
  buildDetectionsGeoJson,
  type ExportRow,
} from "../src/lib/exports";
import { DEMO_DETECTIONS, DEMO_PROVENANCE } from "../src/data/demoData";

const rows: ExportRow[] = DEMO_DETECTIONS.map((d) => ({
  detection: d,
  reviewStatus: d.defaultReview,
}));

describe("exports", () => {
  it("CSV includes a header and one row per detection", () => {
    const csv = buildDetectionsCsv(rows, DEMO_PROVENANCE);
    const lines = csv.trim().split("\n");
    expect(lines.length).toBe(DEMO_DETECTIONS.length + 1);
    expect(lines[0]).toContain("detection_id");
    expect(lines[0]).toContain("demonstration_only");
  });

  it("CSV labels every row demonstrationOnly=true", () => {
    const csv = buildDetectionsCsv(rows, DEMO_PROVENANCE);
    const dataLines = csv.trim().split("\n").slice(1);
    for (const line of dataLines) {
      expect(line.endsWith(",true")).toBe(true);
    }
  });

  it("CSV keeps rejected and uncertain detections visible", () => {
    const csv = buildDetectionsCsv(rows, DEMO_PROVENANCE);
    expect(csv).toContain("rejected");
    expect(csv).toContain("uncertain");
  });

  it("GeoJSON is valid and marks demonstrationOnly", () => {
    const geo = JSON.parse(buildDetectionsGeoJson(rows, DEMO_PROVENANCE));
    expect(geo.type).toBe("FeatureCollection");
    expect(geo.features.length).toBe(DEMO_DETECTIONS.length);
    for (const f of geo.features) {
      expect(f.properties.demonstrationOnly).toBe(true);
      expect(f.geometry.type).toBe("Point");
    }
  });
});
