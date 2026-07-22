// Graphics capability detection and quality tiers (spec §10).

export type QualityTier = "high" | "balanced" | "minimal" | "unsupported";

export interface TierBudget {
  dprCeiling: number;
  segments: number;
  particles: number;
}

export const TIER_BUDGETS: Record<
  Exclude<QualityTier, "unsupported">,
  TierBudget
> = {
  high: { dprCeiling: 1.75, segments: 96, particles: 260 },
  balanced: { dprCeiling: 1.4, segments: 64, particles: 150 },
  minimal: { dprCeiling: 1.15, segments: 36, particles: 70 },
};

interface NavigatorWithExtras extends Navigator {
  deviceMemory?: number;
  connection?: { saveData?: boolean };
}

export function hasWebGL2(): boolean {
  if (typeof document === "undefined") return false;
  try {
    const canvas = document.createElement("canvas");
    return !!canvas.getContext("webgl2");
  } catch {
    return false;
  }
}

export function prefersReducedMotion(): boolean {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function detectTier(): QualityTier {
  if (typeof window === "undefined") return "unsupported";
  if (!hasWebGL2()) return "unsupported";

  const nav = navigator as NavigatorWithExtras;
  const saveData = nav.connection?.saveData === true;
  const memory = nav.deviceMemory ?? 4;
  const cores = nav.hardwareConcurrency ?? 4;

  if (prefersReducedMotion() || saveData || memory <= 2 || cores <= 2) {
    // Reduced-motion still renders the CSS/2D fallback, but if WebGL is used
    // at all, keep it minimal.
    return "minimal";
  }
  if (memory >= 8 && cores >= 8) return "high";
  return "balanced";
}

// Automatic downgrade ladder. Never upgrades within a session (spec §10).
export function nextLowerTier(tier: QualityTier): QualityTier | null {
  if (tier === "high") return "balanced";
  if (tier === "balanced") return "minimal";
  return null;
}
