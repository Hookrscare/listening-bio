import { useAudio } from "../../providers/AudioProvider";
import { useExperience } from "../../providers/ExperienceProvider";
import { track } from "../../lib/analytics";

function BrandMark() {
  return (
    <a className="brand" href="#top" aria-label="Listening.bio home">
      <span className="brand-signal" aria-hidden="true">
        <i />
        <i />
        <i />
        <i />
        <i />
      </span>
      <strong>
        listening<span>.bio</span>
      </strong>
    </a>
  );
}

export function SensoryControls() {
  const { muted, toggleMute } = useAudio();
  const { quietMode, toggleQuietMode } = useExperience();

  return (
    <div className="sensory-controls" role="group" aria-label="Sensory controls">
      <button
        type="button"
        className="sensory-btn"
        aria-pressed={muted}
        onClick={toggleMute}
        title={muted ? "Unmute audio" : "Mute audio"}
      >
        <span aria-hidden="true">{muted ? "🔇" : "🔊"}</span>
        <span>{muted ? "Muted" : "Sound"}</span>
      </button>
      <button
        type="button"
        className="sensory-btn"
        aria-pressed={quietMode}
        onClick={toggleQuietMode}
        title="Quiet mode reduces motion and audio"
      >
        <span aria-hidden="true">{quietMode ? "🌙" : "✦"}</span>
        <span>Quiet</span>
      </button>
    </div>
  );
}

export function Header() {
  return (
    <header className="site-header">
      <BrandMark />
      <nav className="header-nav" aria-label="Primary">
        <a href="#evidence">Evidence</a>
        <a href="#pilot">Pilot</a>
        <a href="#method">Method</a>
        <a href="#partners">Partners</a>
      </nav>
      <div className="header-right">
        <SensoryControls />
        <a
          className="header-action"
          href="#contact"
          onClick={() => track("hero_pilot_cta_clicked", { location: "header" })}
        >
          Discuss a pilot
        </a>
      </div>
    </header>
  );
}
