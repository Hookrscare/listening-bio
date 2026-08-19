import { describe, expect, it } from "vitest";
import { createElement } from "react";
import { SPECIES_PRESETS } from "../src/lib/bioacousticSynth";
import { render, screen } from "@testing-library/react";
import { RoiCalculator } from "../src/components/sections/RoiCalculator";

describe("Bioacoustic Features & Presets", () => {
  it("includes all core species with valid frequency ranges and confidence scores", () => {
    expect(SPECIES_PRESETS.length).toBeGreaterThanOrEqual(5);

    for (const preset of SPECIES_PRESETS) {
      expect(preset.id).toBeTruthy();
      expect(preset.name).toBeTruthy();
      expect(preset.scientificName).toBeTruthy();
      expect(preset.confidence).toBeGreaterThan(0);
      expect(preset.confidence).toBeLessThanOrEqual(1);
      expect(preset.frequencyRange).toContain("Hz");
    }
  });

  it("contains American Robin with Turdidae taxonomic family", () => {
    const robin = SPECIES_PRESETS.find((p) => p.id === "robin");
    expect(robin).toBeDefined();
    expect(robin?.scientificName).toBe("Turdus migratorius");
    expect(robin?.family).toBe("Turdidae");
  });

  it("labels financial outputs as an illustrative planning scenario", () => {
    render(createElement(RoiCalculator));
    expect(screen.getByText("Pilot planning scenario")).toBeInTheDocument();
    expect(screen.getByText("Scenario assumptions")).toBeInTheDocument();
    expect(screen.getByText(/not a certification or compliance determination/i)).toBeInTheDocument();
    expect(screen.queryByText(/audit ready/i)).not.toBeInTheDocument();
  });
});
