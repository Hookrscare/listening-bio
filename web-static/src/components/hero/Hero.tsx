import { Suspense, lazy, useState } from "react";
import { SignalField } from "./SignalField";
import { useExperience } from "../../providers/ExperienceProvider";
import { useAudio } from "../../providers/AudioProvider";
import { track } from "../../lib/analytics";
import { playBioacousticSound } from "../../lib/bioacousticSynth";

const HeroCanvas = lazy(() => import("./HeroCanvas"));

const HERO_SOUND_CHIPS = [
  { id: "robin", label: "Robin pattern", freq: "Synthesized" },
  { id: "thrush", label: "Thrush pattern", freq: "Synthesized" },
  { id: "owl", label: "Owl pattern", freq: "Synthesized" },
  { id: "chorus", label: "Dawn chorus", freq: "Synthesized" },
];

export function Hero() {
  const { quality, motionSuppressed } = useExperience();
  const { energyRef } = useAudio();
  const [playingChip, setPlayingChip] = useState<string | null>(null);

  const useWebGL = quality !== "unsupported" && !motionSuppressed;
  const fallback = <SignalField />;

  const handleChipPlay = (chip: typeof HERO_SOUND_CHIPS[0]) => {
    setPlayingChip(chip.id);
    track("hero_sound_chip_played", { species: chip.label });

    playBioacousticSound(chip.id, (fft) => {
      // Feed instant frequency energy into audio energyRef
      let sum = 0;
      for (let i = 0; i < fft.length; i++) {
        sum += (fft[i] + 100) / 100;
      }
      energyRef.current = Math.min(1.5, (sum / fft.length) * 1.8);
    });

    setTimeout(() => {
      setPlayingChip(null);
      energyRef.current = 0;
    }, 2400);
  };

  return (
    <section className="hero" id="top" aria-label="Hero Section">
      <div className="hero-telemetry-bar" aria-label="Founding pilot scope">
        <span className="telemetry-live-dot" />
        <span className="telemetry-item"><strong>FOUNDING PILOT:</strong> PARTNER SELECTION OPEN</span>
        <span className="telemetry-divider telemetry-secondary">/</span>
        <span className="telemetry-item telemetry-secondary">3–5 SITES PLANNED</span>
        <span className="telemetry-divider telemetry-secondary">/</span>
        <span className="telemetry-item telemetry-secondary">50–100 WAV TARGET</span>
        <span className="telemetry-divider telemetry-secondary">/</span>
        <span className="telemetry-badge telemetry-secondary">FRAMEWORK-INFORMED EVIDENCE DRAFTS</span>
      </div>

      {/* 3D Visual Mesh */}
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
        <p className="eyebrow hero-eyebrow-glow">Reviewable acoustic biodiversity evidence</p>
        <h1 className="hero-headline-gradient">
          Nature leaves a signal.<br />
          We make it <em>reviewable.</em>
        </h1>
        <p className="hero-deck">
          Listening.bio connects environmental recordings to model provenance,
          human decisions, mapped observations, and exportable evidence for land
          managers, researchers, and environmental teams.
        </p>

        <div className="hero-sound-chips-container">
          <span className="chips-label">Play synthesized acoustic demonstrations</span>
          <div className="chips-row">
            {HERO_SOUND_CHIPS.map((chip) => (
              <button
                key={chip.id}
                type="button"
                className={`hero-sound-chip ${playingChip === chip.id ? "playing" : ""}`}
                onClick={() => handleChipPlay(chip)}
              >
                <span className="chip-play-icon">{playingChip === chip.id ? "❚❚" : "▶"}</span>
                <span className="chip-name">{chip.label}</span>
                <span className="chip-freq">{chip.freq}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="hero-actions">
          <a
            className="primary hero-primary-btn"
            href="#enterprise-roi"
            onClick={() => track("hero_roi_cta_clicked", { location: "hero" })}
          >
            Explore pilot economics <span aria-hidden="true">↗</span>
          </a>
          <a className="secondary" href="#soundboard">
            Launch Audio Lab <span aria-hidden="true">↓</span>
          </a>
        </div>

        <div className="hero-trust-row">
          <span>✓ Source WAV SHA-256</span>
          <span>✓ Append-only review history</span>
          <span>✓ Framework-informed draft exports</span>
        </div>
      </div>

      <div className="hero-cockpit-card" aria-hidden="true">
        <div className="cockpit-header">
          <span className="cockpit-title">PILOT SCENARIO / NYC-01</span>
          <span className="cockpit-status">DEMONSTRATION</span>
        </div>
        <div className="cockpit-stats">
          <div>
            <span>PROPOSED SCOPE</span>
            <strong>3–5 PARTNER-APPROVED SITES</strong>
          </div>
          <div>
            <span>NEXT REQUIRED PROOF</span>
            <strong>REVIEWED LOCAL FIELD DATA</strong>
          </div>
        </div>
        <div className="cockpit-mini-waveform">
          <span style={{ height: "45%" }} />
          <span style={{ height: "75%" }} />
          <span style={{ height: "90%" }} />
          <span style={{ height: "60%" }} />
          <span style={{ height: "100%" }} />
          <span style={{ height: "80%" }} />
          <span style={{ height: "40%" }} />
          <span style={{ height: "70%" }} />
          <span style={{ height: "95%" }} />
          <span style={{ height: "50%" }} />
        </div>
        <span className="cockpit-preview-label">SYNTHESIZED SIGNAL PREVIEW</span>
      </div>
    </section>
  );
}
