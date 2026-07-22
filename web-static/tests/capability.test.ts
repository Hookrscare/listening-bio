import { describe, expect, it } from "vitest";
import { TIER_BUDGETS, nextLowerTier } from "../src/lib/capability";

describe("capability tiers (§10)", () => {
  it("high downgrades to balanced, balanced to minimal, minimal terminal", () => {
    expect(nextLowerTier("high")).toBe("balanced");
    expect(nextLowerTier("balanced")).toBe("minimal");
    expect(nextLowerTier("minimal")).toBeNull();
    expect(nextLowerTier("unsupported")).toBeNull();
  });

  it("budgets descend across tiers", () => {
    expect(TIER_BUDGETS.high.particles).toBeGreaterThan(
      TIER_BUDGETS.balanced.particles,
    );
    expect(TIER_BUDGETS.balanced.particles).toBeGreaterThan(
      TIER_BUDGETS.minimal.particles,
    );
    expect(TIER_BUDGETS.high.segments).toBeGreaterThan(
      TIER_BUDGETS.minimal.segments,
    );
    expect(TIER_BUDGETS.high.dprCeiling).toBeGreaterThan(
      TIER_BUDGETS.minimal.dprCeiling,
    );
  });
});
