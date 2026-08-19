import { useState, useRef, useEffect } from "react";
import { SPECIES_PRESETS, playBioacousticSound, type SpeciesPreset } from "../../lib/bioacousticSynth";

export function InteractiveSoundboard() {
  const [selectedSpecies, setSelectedSpecies] = useState<SpeciesPreset>(SPECIES_PRESETS[0]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [reviewState, setReviewState] = useState<Record<string, string>>({
    robin: "confirmed",
    cardinal: "confirmed",
    thrush: "uncertain",
    owl: "unreviewed",
    chorus: "confirmed",
  });
  const [confidenceFilter, setConfidenceFilter] = useState(0.5);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stopAudioRef = useRef<(() => void) | null>(null);
  const freqDataRef = useRef<Float32Array>(new Float32Array(64));

  const handlePlay = (preset: SpeciesPreset) => {
    if (stopAudioRef.current) {
      stopAudioRef.current();
    }
    setSelectedSpecies(preset);
    setIsPlaying(true);

    const stop = playBioacousticSound(preset.id, (fft) => {
      freqDataRef.current = fft;
    });
    stopAudioRef.current = stop;

    setTimeout(() => {
      setIsPlaying(false);
    }, 2800);
  };

  const handleReview = (presetId: string, status: string) => {
    setReviewState((prev) => ({ ...prev, [presetId]: status }));
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrame: number;

    const render = () => {
      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);

      // Background grid
      ctx.strokeStyle = "rgba(114, 242, 199, 0.08)";
      ctx.lineWidth = 1;
      for (let y = 0; y < height; y += 20) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // Live FFT spectrum bars
      const fft = freqDataRef.current;
      const barCount = 36;
      const barWidth = width / barCount;

      for (let i = 0; i < barCount; i++) {
        const val = isPlaying ? Math.max(0, (fft[i] + 90) / 70) : Math.sin(Date.now() * 0.003 + i * 0.4) * 0.15 + 0.2;
        const barHeight = Math.min(height * 0.85, Math.max(4, val * height * 0.8));
        const x = i * barWidth;
        const y = height - barHeight;

        // Gradient styling
        const gradient = ctx.createLinearGradient(0, height, 0, y);
        gradient.addColorStop(0, "rgba(114, 242, 199, 0.2)");
        gradient.addColorStop(0.7, "rgba(183, 255, 101, 0.75)");
        gradient.addColorStop(1, "rgba(255, 255, 255, 0.95)");

        ctx.fillStyle = gradient;
        ctx.fillRect(x + 2, y, barWidth - 4, barHeight);

        // Neon cap
        ctx.fillStyle = "#b7ff65";
        ctx.fillRect(x + 2, y - 2, barWidth - 4, 2);
      }

      // Detection Candidate Bounding Box
      const boxX = width * 0.25;
      const boxY = height * 0.18;
      const boxW = width * 0.5;
      const boxH = height * 0.6;

      ctx.strokeStyle = isPlaying ? "#b7ff65" : "rgba(183, 255, 101, 0.4)";
      ctx.lineWidth = 2;
      ctx.strokeRect(boxX, boxY, boxW, boxH);

      ctx.fillStyle = isPlaying ? "rgba(183, 255, 101, 0.12)" : "rgba(183, 255, 101, 0.03)";
      ctx.fillRect(boxX, boxY, boxW, boxH);

      // Detection Label HUD
      ctx.fillStyle = "#b7ff65";
      ctx.font = "600 11px ui-monospace, SFMono-Regular, monospace";
      ctx.fillText(
        `[ CANDIDATE: ${selectedSpecies.name.toUpperCase()} — CONF: ${Math.round(selectedSpecies.confidence * 100)}% ]`,
        boxX + 8,
        boxY - 8
      );

      animationFrame = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrame);
    };
  }, [isPlaying, selectedSpecies]);

  return (
    <div className="interactive-soundboard-container" id="soundboard">
      <div className="soundboard-header">
        <div>
          <span className="eyebrow">Interactive Live Audio Lab</span>
          <h3>Bioacoustic Species Soundboard</h3>
          <p className="subtitle">
            Experience real-time frequency analysis and transparent verification across field species.
          </p>
        </div>

        <div className="confidence-slider-box">
          <label htmlFor="confidence-filter">
            Confidence Filter: <strong>{Math.round(confidenceFilter * 100)}%</strong>
          </label>
          <input
            id="confidence-filter"
            type="range"
            min="0.1"
            max="0.95"
            step="0.05"
            value={confidenceFilter}
            onChange={(e) => setConfidenceFilter(parseFloat(e.target.value))}
          />
        </div>
      </div>

      <div className="soundboard-grid">
        {/* Left: Species List */}
        <div className="species-list" role="tablist" aria-label="Bioacoustic species selector">
          {SPECIES_PRESETS.map((preset) => {
            const currentStatus = reviewState[preset.id] || "unreviewed";
            const isSelected = selectedSpecies.id === preset.id;
            const matchesFilter = preset.confidence >= confidenceFilter;

            return (
              <button
                key={preset.id}
                type="button"
                role="tab"
                aria-selected={isSelected}
                className={`species-card-btn ${isSelected ? "selected" : ""} ${!matchesFilter ? "dimmed" : ""}`}
                onClick={() => handlePlay(preset)}
              >
                <div className="species-info">
                  <div className="species-title-row">
                    <strong>{preset.name}</strong>
                    <span className={`status-badge ${currentStatus}`}>{currentStatus}</span>
                  </div>
                  <span className="scientific-name"><em>{preset.scientificName}</em></span>
                  <div className="tags-row">
                    <span className="mini-tag">{preset.frequencyRange}</span>
                    <span className="conf-tag">{Math.round(preset.confidence * 100)}% conf</span>
                  </div>
                </div>

                <div className="play-indicator">
                  {isPlaying && isSelected ? <span className="audio-wave-anim" /> : "▶"}
                </div>
              </button>
            );
          })}
        </div>

        {/* Right: Real-time Audio Visualizer & Verification Station */}
        <div className="visualizer-station">
          <div className="station-hud">
            <div className="hud-metric">
              <span>TARGET SPECIES</span>
              <strong>{selectedSpecies.name}</strong>
            </div>
            <div className="hud-metric">
              <span>BANDWIDTH</span>
              <strong>{selectedSpecies.frequencyRange}</strong>
            </div>
            <div className="hud-metric">
              <span>INFERENCE MODEL</span>
              <strong>BirdNET v2.4 Native</strong>
            </div>
            <div className="hud-metric">
              <span>PROVENANCE</span>
              <strong className="verified-text">Auditable WAV</strong>
            </div>
          </div>

          <div className="canvas-wrapper">
            <canvas ref={canvasRef} width={640} height={240} className="spectrogram-canvas" />
          </div>

          <div className="station-controls">
            <div className="playback-buttons">
              <button
                type="button"
                className="primary-play-btn"
                onClick={() => handlePlay(selectedSpecies)}
              >
                {isPlaying ? "■ Playing Biophony Stream..." : `▶ Play ${selectedSpecies.name}`}
              </button>
            </div>

            <div className="human-review-actions">
              <span className="review-label">Expert Human Verification:</span>
              <div className="btn-group">
                <button
                  type="button"
                  className={`review-btn confirm ${reviewState[selectedSpecies.id] === "confirmed" ? "active" : ""}`}
                  onClick={() => handleReview(selectedSpecies.id, "confirmed")}
                >
                  ✓ Confirm
                </button>
                <button
                  type="button"
                  className={`review-btn uncertain ${reviewState[selectedSpecies.id] === "uncertain" ? "active" : ""}`}
                  onClick={() => handleReview(selectedSpecies.id, "uncertain")}
                >
                  ? Uncertain
                </button>
                <button
                  type="button"
                  className={`review-btn reject ${reviewState[selectedSpecies.id] === "rejected" ? "active" : ""}`}
                  onClick={() => handleReview(selectedSpecies.id, "rejected")}
                >
                  ✕ Reject
                </button>
              </div>
            </div>
          </div>

          <div className="station-footnote">
            <p>
              <strong>Scientific Governance Principle:</strong> Detections are candidate evidence until validated by
              expert human review or secondary sensors.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
