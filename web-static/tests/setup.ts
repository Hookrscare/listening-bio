import "@testing-library/jest-dom/vitest";

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
