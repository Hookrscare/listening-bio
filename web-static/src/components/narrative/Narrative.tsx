import { type ReactNode, useEffect, useRef, useState } from "react";
import { useNarrativeState } from "./useNarrativeState";
import { useExperience } from "../../providers/ExperienceProvider";
import {
  ReviewMatrix,
  SignalConstellation,
  SiteNetwork,
} from "./ChapterVisuals";

interface Chapter {
  index: number;
  kicker: string;
  heading: string;
  summary: string;
  question: string;
  core: string;
  visual: ReactNode;
}

const CHAPTERS: Chapter[] = [
  {
    index: 0,
    kicker: "Chapter 1 — Listen",
    heading: "A habitat is never silent.",
    summary:
      "Environmental sound carries evidence across hours, weather, seasons, and species activity that short surveys may not capture.",
    question: "What is present here?",
    core: "A recording is not yet a biodiversity conclusion. It is a durable source record that can be revisited and reviewed.",
    visual: (
      <div className="chapter-visual">
        <SignalConstellation />
        <div className="node-legend">
          <span>Broad habitat field</span>
          <span>Low signal clarity</span>
        </div>
      </div>
    ),
  },
  {
    index: 1,
    kicker: "Chapter 2 — Detect",
    heading: "The system proposes. It does not conclude.",
    summary:
      "BirdNET identifies candidate vocalizations and preserves their time windows, confidence, source context, and processing configuration.",
    question: "What might the system have heard?",
    core: "Source preserved. Configuration recorded. Uncertainty visible. Confidence supports triage — prediction does not equal confirmation.",
    visual: (
      <div className="chapter-visual">
        <SignalConstellation />
        <div className="node-legend">
          <span>Candidate nodes emerging</span>
          <span>Confidence + timing visible</span>
        </div>
      </div>
    ),
  },
  {
    index: 2,
    kicker: "Chapter 3 — Review",
    heading: "Evidence becomes useful when it can be challenged.",
    summary:
      "A reviewer can hear the source, inspect the signal, assess confidence, preserve uncertainty, and record a defensible decision.",
    question: "Does the evidence support the label?",
    core: "Confirmed, rejected, and uncertain candidates remain part of the record. Review never overwrites the original model result.",
    visual: (
      <div className="chapter-visual">
        <ReviewMatrix />
      </div>
    ),
  },
  {
    index: 3,
    kicker: "Chapter 4 — Act",
    heading: "The result must support a real decision.",
    summary:
      "Structured evidence can inform stewardship, restoration, education, field planning, and larger monitoring programs.",
    question: "What should happen next?",
    core: "Stewardship decisions, restoration monitoring, biodiversity baselines, education, community science, follow-up surveys, and funding readiness.",
    visual: (
      <div className="chapter-visual">
        <SiteNetwork />
        <div className="node-legend">
          <span>Representative simulation sites</span>
          <span>Not field evidence</span>
        </div>
      </div>
    ),
  },
];

export function Narrative() {
  const { activeIndex } = useNarrativeState(CHAPTERS.length);
  const { motionSuppressed } = useExperience();
  const narrativeRef = useRef<HTMLDivElement>(null);
  const [railVisible, setRailVisible] = useState(false);

  useEffect(() => {
    const element = narrativeRef.current;
    if (!element || typeof IntersectionObserver === "undefined") return;

    const observer = new IntersectionObserver(
      ([entry]) => setRailVisible(entry.isIntersecting),
      { rootMargin: "-15% 0px -15% 0px" },
    );
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const jump = (index: number) => {
    document
      .getElementById(`chapter-${index}`)
      ?.scrollIntoView({ behavior: motionSuppressed ? "auto" : "smooth" });
  };

  return (
    <div
      ref={narrativeRef}
      className="narrative"
      aria-label="Listen, Detect, Review, Act"
    >
      {railVisible && (
        <nav className="chapter-rail is-visible" aria-label="Narrative progress">
          {CHAPTERS.map((c) => (
            <button
              key={c.index}
              type="button"
              aria-current={activeIndex === c.index}
              onClick={() => jump(c.index)}
            >
              <span className="tick" aria-hidden="true" />
              {c.kicker.split("—")[1]?.trim() ?? c.heading}
            </button>
          ))}
        </nav>
      )}

      {CHAPTERS.map((c) => (
        <section
          key={c.index}
          id={`chapter-${c.index}`}
          className="chapter"
          data-chapter-index={c.index}
          aria-labelledby={`chapter-${c.index}-heading`}
        >
          <div className="chapter-copy">
            <p className="chapter-index">{c.kicker}</p>
            <h2 id={`chapter-${c.index}-heading`}>{c.heading}</h2>
            <p className="chapter-summary">{c.summary}</p>
            <p className="chapter-question">{c.question}</p>
            <p className="chapter-core">{c.core}</p>
          </div>
          {c.visual}
        </section>
      ))}
    </div>
  );
}
