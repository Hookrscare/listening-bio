import { describe, expect, it } from "vitest";
import { buildPartnerEmail } from "../src/components/sections/Contact";

describe("partner enquiry fallback", () => {
  it("prepares a complete Listening.bio email draft without a public API", () => {
    const href = buildPartnerEmail({
      name: "Avery Researcher",
      organization: "Urban Ecology Lab",
      email: "avery@example.org",
      partnership_role: "Scientific collaborator",
    });

    expect(href).toMatch(/^mailto:rodrigo@listening\.bio/);
    expect(decodeURIComponent(href)).toContain("Urban Ecology Lab");
    expect(decodeURIComponent(href)).toContain("Scientific collaborator");
  });
});
