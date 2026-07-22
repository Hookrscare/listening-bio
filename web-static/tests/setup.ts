import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";

// Keep capability detection and the decorative 2D fallback quiet in jsdom.
Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
  configurable: true,
  value: vi.fn(() => null),
});

// jsdom lacks IntersectionObserver; provide a no-op stub for component tests.
if (typeof globalThis.IntersectionObserver === "undefined") {
  class IO {
    observe() {}
    unobserve() {}
    disconnect() {}
    takeRecords() {
      return [];
    }
    root = null;
    rootMargin = "";
    thresholds = [];
  }
  globalThis.IntersectionObserver =
    IO as unknown as typeof IntersectionObserver;
}
