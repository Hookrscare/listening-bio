import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  DEMO_AUDIO_SRC,
  DEMO_DETECTIONS,
  DEMO_PROVENANCE,
  DEMO_SPECTROGRAM_SRC,
  type DemoDetection,
  type ReviewStatus,
} from "../../data/demoData";
import { useAudio } from "../../providers/AudioProvider";
import { track } from "../../lib/analytics";
import {
  exportDetectionsCsv,
  exportDetectionsGeoJson,
  type ExportRow,
} from "../../lib/exports";

const REVIEW_STATES: ReviewStatus[] = [
  "unreviewed",
  "confirmed",
  "rejected",
  "uncertain",
];

function fmt(t: number) {
  const m = Math.floor(t / 60);
  const s = Math.floor(t % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

// Deterministic pseudo-waveform bars (representative — the demo clip is short).
function Waveform({
  duration,
  currentTime,
  onSeek,
}: {
  duration: number;
  currentTime: number;
  onSeek: (t: number) => void;
}) {
  const bars = useMemo(() => {
    const n = 120;
    return Array.from({ length: n }, (_, i) => {
      const env = Math.sin((i / n) * Math.PI);
      return 0.15 + Math.abs(Math.sin(i * 0.7) * 0.5 + Math.sin(i * 0.23) * 0.4) * env;
    });
  }, []);
  const progress = duration ? currentTime / duration : 0;

  return (
    <svg
      className="evidence-waveform"
      viewBox="0 0 120 40"
      preserveAspectRatio="none"
      role="slider"
      aria-label="Audio waveform seek"
      aria-valuemin={0}
      aria-valuemax={Math.round(duration)}
      aria-valuenow={Math.round(currentTime)}
      tabIndex={0}
      onClick={(e) => {
        const rect = (e.currentTarget as SVGElement).getBoundingClientRect();
        const ratio = (e.clientX - rect.left) / rect.width;
        onSeek(ratio * duration);
      }}
    >
      {bars.map((h, i) => {
        const active = i / bars.length <= progress;
        return (
          <rect
            key={i}
            x={i}
            y={20 - h * 18}
            width={0.7}
            height={h * 36}
            fill={active ? "#b7ff65" : "rgba(114,242,199,0.35)"}
          />
        );
      })}
    </svg>
  );
}

export function EvidenceDemo() {
  const {
    load,
    play,
    pause,
    seek,
    isPlaying,
    currentTime,
    duration,
    error,
    muted,
    toggleMute,
  } = useAudio();

  const [selectedId, setSelectedId] = useState<string>(DEMO_DETECTIONS[0].id);
  const [reviews, setReviews] = useState<Record<string, ReviewStatus>>(() =>
    Object.fromEntries(DEMO_DETECTIONS.map((d) => [d.id, d.defaultReview])),
  );
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [started, setStarted] = useState(false);
  const [provenanceOpen, setProvenanceOpen] = useState(false);
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    load(DEMO_AUDIO_SRC);
  }, [load]);

  const selected = DEMO_DETECTIONS.find((d) => d.id === selectedId)!;
  const effectiveDuration = duration || 27; // representative fallback length

  const markStarted = useCallback(() => {
    if (!started) {
      setStarted(true);
      track("evidence_demo_started");
    }
  }, [started]);

  const onPlayPause = useCallback(() => {
    markStarted();
    if (isPlaying) pause();
    else void play();
  }, [isPlaying, pause, play, markStarted]);

  const selectDetection = useCallback(
    (d: DemoDetection) => {
      setSelectedId(d.id);
      track("detection_selected", { source: "evidence", label: d.label });
      // Focus-window listening: seek to just before the candidate.
      seek(Math.max(0, d.startSeconds - 0.3));
    },
    [seek],
  );

  const setReview = useCallback((id: string, status: ReviewStatus) => {
    setReviews((prev) => ({ ...prev, [id]: status }));
    track("review_status_changed", { status });
  }, []);

  const exportRows: ExportRow[] = useMemo(
    () =>
      DEMO_DETECTIONS.map((d) => ({
        detection: d,
        reviewStatus: reviews[d.id],
      })),
    [reviews],
  );

  // Keyboard: Space play/pause, arrows seek, Home/End (spec §12) — only when
  // focus is within the workspace and not on a form control.
  const onKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const isFormControl = /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName);
      if (isFormControl && e.key !== "Home" && e.key !== "End") return;
      switch (e.key) {
        case " ":
          e.preventDefault();
          onPlayPause();
          break;
        case "ArrowLeft":
          e.preventDefault();
          seek(currentTime - 5);
          break;
        case "ArrowRight":
          e.preventDefault();
          seek(currentTime + 5);
          break;
        case "Home":
          e.preventDefault();
          seek(0);
          break;
        case "End":
          e.preventDefault();
          seek(effectiveDuration);
          break;
      }
    },
    [onPlayPause, seek, currentTime, effectiveDuration],
  );

  return (
    <section
      className="evidence"
      id="evidence"
      ref={sectionRef}
      aria-labelledby="evidence-heading"
      onKeyDown={onKeyDown}
    >
      <p className="eyebrow">Interactive evidence</p>
      <h2 id="evidence-heading">Hear it. Inspect it. Decide.</h2>

      <div className="evidence-warning" role="note">
        <span aria-hidden="true">▲</span>
        <p>
          <strong>Representative demonstration data.</strong> These candidate
          detections illustrate the review workflow only. They are not a
          scientific finding and imply no site-level biodiversity conclusion.
          Exports are labeled <code>demonstrationOnly</code>.
        </p>
      </div>

      <div className="evidence-workspace">
        <div className="evidence-main">
          <div className="evidence-visual">
            <img
              className="evidence-spectrogram"
              src={DEMO_SPECTROGRAM_SRC}
              alt={`Spectrogram of ${DEMO_PROVENANCE.recordingTitle}. Horizontal axis is time, vertical axis is frequency; brighter bands show candidate American Robin phrases between roughly 1.7 and 3.6 kHz.`}
            />
            {/* Candidate bands over the spectrogram */}
            {DEMO_DETECTIONS.map((d) => {
              const left = (d.startSeconds / effectiveDuration) * 100;
              const width =
                ((d.endSeconds - d.startSeconds) / effectiveDuration) * 100;
              return (
                <button
                  key={d.id}
                  type="button"
                  className="evidence-marker-band"
                  style={{ left: `${left}%`, width: `${width}%` }}
                  aria-pressed={selectedId === d.id}
                  aria-label={`Candidate ${d.label}, confidence ${d.confidence}, ${d.startSeconds} to ${d.endSeconds} seconds`}
                  onClick={() => selectDetection(d)}
                />
              );
            })}
            <div
              className="evidence-playhead"
              style={{ left: `${(currentTime / effectiveDuration) * 100}%` }}
              aria-hidden="true"
            />
          </div>

          <Waveform
            duration={effectiveDuration}
            currentTime={currentTime}
            onSeek={seek}
          />

          <div className="evidence-controls">
            <button
              type="button"
              className="transport-btn"
              onClick={onPlayPause}
              aria-label={isPlaying ? "Pause" : "Play"}
            >
              {isPlaying ? "❚❚ Pause" : "► Play"}
            </button>
            <button
              type="button"
              className="transport-btn"
              onClick={() => seek(currentTime - 5)}
              aria-label="Back five seconds"
            >
              −5s
            </button>
            <button
              type="button"
              className="transport-btn"
              onClick={() => seek(currentTime + 5)}
              aria-label="Forward five seconds"
            >
              +5s
            </button>
            <button
              type="button"
              className="transport-btn"
              onClick={toggleMute}
              aria-pressed={muted}
              aria-label={muted ? "Unmute" : "Mute"}
            >
              {muted ? "🔇" : "🔊"}
            </button>
            <input
              className="evidence-seek"
              type="range"
              min={0}
              max={Math.round(effectiveDuration)}
              step={0.1}
              value={currentTime}
              onChange={(e) => seek(Number(e.target.value))}
              aria-label="Seek through recording"
            />
            <span className="time">
              {fmt(currentTime)} / {fmt(effectiveDuration)}
            </span>
          </div>

          {error && (
            <p className="form-status error" role="status">
              {error}
            </p>
          )}

          <ul className="candidate-list">
            {DEMO_DETECTIONS.map((d) => {
              const status = reviews[d.id];
              const isActive = selectedId === d.id;
              return (
                <li
                  key={d.id}
                  className={`candidate-row ${isActive ? "active" : ""}`}
                >
                  <button
                    type="button"
                    className="candidate-head"
                    aria-expanded={isActive}
                    onClick={() => selectDetection(d)}
                  >
                    <span className="label">
                      {d.label}
                      {d.scientificName ? ` · ${d.scientificName}` : ""}
                    </span>
                    <span className="meta">
                      {d.confidence.toFixed(2)} · {d.startSeconds}–{d.endSeconds}s
                    </span>
                    <span className={`status-badge ${status}`}>{status}</span>
                  </button>

                  {isActive && (
                    <div className="candidate-detail">
                      <p className="chapter-core" style={{ marginTop: 0 }}>
                        Confidence {d.confidence.toFixed(2)} · window{" "}
                        {d.startSeconds}–{d.endSeconds}s · frequency{" "}
                        {d.frequencyMinHz}–{d.frequencyMaxHz} Hz
                      </p>
                      <fieldset className="review-fieldset">
                        <legend>Reviewer decision</legend>
                        <div className="review-options">
                          {REVIEW_STATES.map((s) => (
                            <label key={s}>
                              <input
                                type="radio"
                                name={`review-${d.id}`}
                                value={s}
                                checked={status === s}
                                onChange={() => setReview(d.id, s)}
                              />
                              {s}
                            </label>
                          ))}
                        </div>
                      </fieldset>
                      <label
                        className="visually-hidden"
                        htmlFor={`note-${d.id}`}
                      >
                        Reviewer note (stays on this device)
                      </label>
                      <textarea
                        id={`note-${d.id}`}
                        className="review-note"
                        placeholder="Reviewer note (kept locally on your device, never uploaded)…"
                        value={notes[d.id] ?? ""}
                        onChange={(e) =>
                          setNotes((prev) => ({
                            ...prev,
                            [d.id]: e.target.value,
                          }))
                        }
                      />
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        </div>

        <aside className="evidence-side">
          <div className="provenance-panel">
            <h3>Evidence provenance</h3>
            <button
              type="button"
              className="ghost-btn"
              aria-expanded={provenanceOpen}
              onClick={() => {
                setProvenanceOpen((o) => !o);
                if (!provenanceOpen) track("provenance_panel_opened");
              }}
            >
              {provenanceOpen ? "Hide full provenance" : "Show full provenance"}
            </button>
            {provenanceOpen && (
              <dl className="provenance-dl">
                <div>
                  <dt>Recording ID</dt>
                  <dd>{DEMO_PROVENANCE.recordingId}</dd>
                </div>
                <div>
                  <dt>Title</dt>
                  <dd>{DEMO_PROVENANCE.recordingTitle}</dd>
                </div>
                <div>
                  <dt>Recorded</dt>
                  <dd>{DEMO_PROVENANCE.recordedAt}</dd>
                </div>
                <div>
                  <dt>Location</dt>
                  <dd>{DEMO_PROVENANCE.locationLabel}</dd>
                </div>
                <div>
                  <dt>Latitude</dt>
                  <dd>{DEMO_PROVENANCE.latitude}</dd>
                </div>
                <div>
                  <dt>Longitude</dt>
                  <dd>{DEMO_PROVENANCE.longitude}</dd>
                </div>
                <div>
                  <dt>Habitat</dt>
                  <dd>{DEMO_PROVENANCE.habitat}</dd>
                </div>
                <div>
                  <dt>Recorder</dt>
                  <dd>{DEMO_PROVENANCE.recorder}</dd>
                </div>
                <div>
                  <dt>Sample rate</dt>
                  <dd>{DEMO_PROVENANCE.sampleRateHz} Hz</dd>
                </div>
                <div>
                  <dt>Channels</dt>
                  <dd>{DEMO_PROVENANCE.channelCount}</dd>
                </div>
                <div>
                  <dt>Source license</dt>
                  <dd>
                    <a
                      href={DEMO_PROVENANCE.sourceLicenseUrl}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {DEMO_PROVENANCE.sourceLicense}
                    </a>
                  </dd>
                </div>
                <div>
                  <dt>Source</dt>
                  <dd>
                    <a
                      href={DEMO_PROVENANCE.sourceUrl}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {DEMO_PROVENANCE.sourceUrl}
                    </a>
                  </dd>
                </div>
                <div>
                  <dt>Checksum</dt>
                  <dd>{DEMO_PROVENANCE.fileChecksum}</dd>
                </div>
                <div>
                  <dt>Model</dt>
                  <dd>{DEMO_PROVENANCE.modelName}</dd>
                </div>
                <div>
                  <dt>Model version</dt>
                  <dd>{DEMO_PROVENANCE.modelVersion}</dd>
                </div>
                <div>
                  <dt>Locale</dt>
                  <dd>{DEMO_PROVENANCE.modelLocale}</dd>
                </div>
                <div>
                  <dt>Confidence threshold</dt>
                  <dd>{DEMO_PROVENANCE.confidenceThreshold}</dd>
                </div>
                <div>
                  <dt>Evidence level</dt>
                  <dd>{DEMO_PROVENANCE.evidenceLevel}</dd>
                </div>
              </dl>
            )}
            <p className="attribution">
              Source audio: American Robin, Xeno-canto{" "}
              <a href={DEMO_PROVENANCE.sourceUrl} target="_blank" rel="noreferrer">
                XC364638
              </a>{" "}
              by {DEMO_PROVENANCE.recorder}, licensed{" "}
              <a
                href={DEMO_PROVENANCE.sourceLicenseUrl}
                target="_blank"
                rel="noreferrer"
              >
                CC BY-NC-SA 4.0
              </a>
              .
            </p>
          </div>

          <div className="export-panel">
            <h3>Export evidence</h3>
            <p className="attribution" style={{ marginTop: 4 }}>
              Includes every candidate — confirmed, rejected, and uncertain — and
              carries the <code>demonstrationOnly</code> label.
            </p>
            <div className="export-actions">
              <button
                type="button"
                className="ghost-btn"
                onClick={() => {
                  exportDetectionsCsv(exportRows, DEMO_PROVENANCE);
                  track("export_csv");
                }}
              >
                Export CSV
              </button>
              <button
                type="button"
                className="ghost-btn"
                onClick={() => {
                  exportDetectionsGeoJson(exportRows, DEMO_PROVENANCE);
                  track("export_geojson");
                }}
              >
                Export GeoJSON
              </button>
            </div>
          </div>

          <div className="export-panel">
            <h3>Text equivalent</h3>
            <p className="attribution" style={{ marginTop: 4 }}>
              Currently selected: <strong>{selected.label}</strong> (
              {selected.scientificName}), confidence{" "}
              {selected.confidence.toFixed(2)}, window {selected.startSeconds}–
              {selected.endSeconds}s, frequency {selected.frequencyMinHz}–
              {selected.frequencyMaxHz} Hz, reviewer decision{" "}
              {reviews[selected.id]}. No audio is required to read this evidence.
            </p>
          </div>
        </aside>
      </div>
    </section>
  );
}
