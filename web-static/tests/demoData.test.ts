import { describe, expect, it } from "vitest";
import {
  DEMO_DETECTIONS,
  DEMO_PROVENANCE,
  DEMO_SITES,
} from "../src/data/demoData";

describe("demo data integrity (content-integrity rules §20)", () => {
  it("every detection is flagged demonstrationOnly", () => {
    for (const d of DEMO_DETECTIONS) {
      expect(d.demonstrationOnly).toBe(true);
    }
  });

  it("provenance is flagged demonstrationOnly and uses the real licensed source", () => {
    expect(DEMO_PROVENANCE.demonstrationOnly).toBe(true);
    expect(DEMO_PROVENANCE.recordingId).toBe("XC364638");
    expect(DEMO_PROVENANCE.sourceLicense).toBe("CC BY-NC-SA 4.0");
    expect(DEMO_PROVENANCE.sourceUrl).toContain("xeno-canto.org");
    expect(DEMO_PROVENANCE.recorder).toBe("Ted Floyd");
  });

  it("all four review states are represented", () => {
    const states = new Set(DEMO_DETECTIONS.map((d) => d.defaultReview));
    expect(states.has("confirmed")).toBe(true);
    expect(states.has("rejected")).toBe(true);
    expect(states.has("uncertain")).toBe(true);
    expect(states.has("unreviewed")).toBe(true);
  });

  it("sites are labeled simulation only (no field claims)", () => {
    for (const s of DEMO_SITES) {
      expect(s.evidenceLevel).toBe("simulation");
      expect(s.claimStatus.toLowerCase()).toContain("demo");
    }
  });
});
