import { Suspense, lazy, useState } from "react";
import { SignalField } from "./SignalField";
import { useExperience } from "../../providers/ExperienceProvider";
import { track } from "../../lib/analytics";

const HeroCanvas = lazy(() => import("./HeroCanvas"));

// Accessible, decorative hero markers. Selecting one smooth-scrolls to the
// evidence workspace — the actual reviewable data lives there, in the DOM.
const MARKERS = [
  { id: "m1", label: "American Robin", conf: "0.91", top: "38%", left: "22%" },
  { id: "m2", label: "Candidate call", conf: "0.74", top: "54%", left: "58%" },
  { id: "m3", label: "Ambient signal", conf: "0.52", top: "68%", left: "40%" },
];

export function Hero() {
  const { quality, motionSuppressed } = useExperience();
  const [activeMarker, setActiveMarker] = useState<string | null>(null);

  const useWebGL = quality !== "unsupported" && !motionSuppressed;
  const fallback = <SignalField />;

  const goToEvidence = (markerId: string, label: string) => {
    setActiveMarker(markerId);
    track("detection_selected", { source: "hero", label });
    document
      .getElementById("evidence")
      ?.scrollIntoView({ behavior: motionSuppressed ? "auto" : "smooth" });
  };

  return (
    <section className="hero" id="top">
      <div className="hero-visual" aria-hidden="true">
        {useWebGL ? (
          <Suspense fallback={fallback}>
            <HeroCanvas fallback={fallback} />
          </Suspense>
        ) : (
          fallback
        )}
      </div>

      <div className="hero-grid" aria-hidden="true" />

      <div className="hero-copy">
        <p className="eyebrow">Auditable acoustic biodiversity monitoring</p>
        <h1>
          Listen to nature.
          <br />
          Measure change.
        </h1>
        <p className="hero-deck">
          Listening.bio transforms environmental recordings into transparent,
          reviewable evidence for conservation teams, researchers, and land
          managers.
        </p>
        <div className="hero-actions">
          <a
            className="primary"
            href="#contact"
            onClick={() =>
              track("hero_pilot_cta_clicked", { location: "hero" })
            }
          >
            Discuss a pilot <span aria-hidden="true">↗</span>
          </a>
          <a className="secondary" href="#evidence">
            Explore the evidence <span aria-hidden="true">↓</span>
          </a>
        </div>
        <p className="hero-disclaimer">
          Candidate detections remain connected to source audio, model context,
          and human review. Automated predictions are evidence candidates, not
          final ecological truth.
        </p>
      </div>

      <div className="hero-index" aria-hidden="true">
        <span>FIELD / DEMO 01</span>
        <span>39.9936 N</span>
        <span>105.0897 W</span>
      </div>

      {/* Decorative but keyboard-accessible candidate markers (spec §4). */}
      <div className="hero-markers">
        {MARKERS.map((m) => (
          <button
            key={m.id}
            type="button"
            className="hero-marker"
            style={{ top: m.top, left: m.left }}
            aria-pressed={activeMarker === m.id}
            onClick={() => goToEvidence(m.id, m.label)}
          >
            <span className="dot" aria-hidden="true" />
            {m.label} · {m.conf}
          </button>
        ))}
      </div>

      <div className="principle">
        <span>Our principle</span>
        <strong>
          Automated detections are evidence candidates, not final ecological
          truth.
        </strong>
      </div>
    </section>
  );
}
