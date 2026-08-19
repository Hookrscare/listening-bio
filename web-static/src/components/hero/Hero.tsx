import { Suspense, lazy, useState } from "react";
import { SignalField } from "./SignalField";
import { useExperience } from "../../providers/ExperienceProvider";
import { useAudio } from "../../providers/AudioProvider";
import { track } from "../../lib/analytics";
import { playBioacousticSound } from "../../lib/bioacousticSynth";

const HeroCanvas = lazy(() => import("./HeroCanvas"));

const HERO_SOUND_CHIPS = [
  { id: "robin", label: "American Robin", freq: "2.4 kHz", color: "#b7ff65" },
  { id: "thrush", label: "Wood Thrush", freq: "3.8 kHz", color: "#38bdf8" },
  { id: "owl", label: "Great Horned Owl", freq: "320 Hz", color: "#ffcf6b" },
  { id: "chorus", label: "Dawn Chorus Mix", freq: "Wideband biophony", color: "#72f2c7" },
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
      {/* Live Bioacoustic Telemetry Bar */}
      <div className="hero-telemetry-bar" aria-label="Live Telemetry Feed">
        <span className="telemetry-live-dot" />
        <span className="telemetry-item"><strong>LIVE TELEMETRY:</strong> 4 SITES ACTIVE</span>
        <span className="telemetry-divider">/</span>
        <span className="telemetry-item">1,420 HRS CONTINUOUS AUDIO</span>
        <span className="telemetry-divider">/</span>
        <span className="telemetry-item">94.2% INFERENCE CONFIDENCE</span>
        <span className="telemetry-divider">/</span>
        <span className="telemetry-badge">TNFD & CSRD ESRS E4 COMPLIANT</span>
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
        <p className="eyebrow hero-eyebrow-glow">Auditable Acoustic Biodiversity Monitoring & TNFD Intelligence</p>
        <h1 className="hero-headline-gradient">
          Nature leaves a signal.<br />
          We turn it into <em>proof.</em>
        </h1>
        <p className="hero-deck">
          Listening.bio turns continuous environmental soundscapes into transparent, auditable biodiversity evidence
          for corporate ESG compliance, land trusts, renewable energy, and scientific research.
        </p>

        {/* Live Audio Trigger Chips directly in the Hero */}
        <div className="hero-sound-chips-container">
          <span className="chips-label">▶ Test Instant Bioacoustic Inference:</span>
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
            Calculate Enterprise ROI <span aria-hidden="true">↗</span>
          </a>
          <a className="secondary" href="#soundboard">
            Launch Audio Lab <span aria-hidden="true">↓</span>
          </a>
        </div>

        <div className="hero-trust-row">
          <span>✓ Raw WAV SHA-256 Hashes</span>
          <span>✓ Expert Ecological Validation</span>
          <span>✓ TNFD / CSRD Export Ready</span>
        </div>
      </div>

      {/* Floating Holographic Cockpit Card */}
      <div className="hero-cockpit-card" aria-hidden="true">
        <div className="cockpit-header">
          <span className="cockpit-title">SENSOR NODE NYC-01</span>
          <span className="cockpit-status">ACTIVE STREAM</span>
        </div>
        <div className="cockpit-stats">
          <div>
            <span>COORDINATES</span>
            <strong>40.7829° N, 73.9654° W</strong>
          </div>
          <div>
            <span>BIOPHONY INDEX</span>
            <strong>NDSI: +0.86 (High)</strong>
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
      </div>
    </section>
  );
}
