import { describe, expect, it, vi, beforeAll } from "vitest";
import { render, screen } from "@testing-library/react";
import { App } from "../src/App";

// WebGL/AudioContext are not available in jsdom; the app must still render its
// full DOM content (fallback path) — proving no essential content is WebGL-only.
beforeAll(() => {
  vi.stubGlobal(
    "matchMedia",
    vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  );
});

describe("App renders core content without WebGL/Audio", () => {
  it("shows the hero headline, evidence, pilot, and contact", () => {
    render(<App />);
    expect(
      screen.getByRole("heading", { name: /Nature leaves a signal/i, level: 1 }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Hear it\. Inspect it\. Decide\./i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /\$10,000 pilot/i }),
    ).toBeInTheDocument();
    // Contact form present with required fields
    expect(screen.getByLabelText(/Name \*/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email \*/i)).toBeInTheDocument();
  });

  it("shows the demonstration-only warning (content integrity)", () => {
    render(<App />);
    expect(
      screen.getAllByText(/Representative demonstration data/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(/Partner selection open/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Governance terms remain drafts/i),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Live telemetry/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/ESRS E4 compliant/i)).not.toBeInTheDocument();
  });

  it("keeps rejected and uncertain candidates visible", () => {
    render(<App />);
    expect(screen.getAllByText(/rejected/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/uncertain/i).length).toBeGreaterThan(0);
  });
});
