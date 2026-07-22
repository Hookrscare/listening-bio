import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { track } from "../lib/analytics";
import { useExperience } from "./ExperienceProvider";

interface AudioState {
  // Consent / mute (AudioProvider concern)
  consentGranted: boolean;
  grantConsent: () => void;
  muted: boolean;
  toggleMute: () => void;
  volume: number;
  setVolume: (v: number) => void;
  effectiveVolume: number;

  // Engine (AudioEngineProvider concern)
  load: (src: string) => void;
  play: () => Promise<void>;
  pause: () => void;
  seek: (seconds: number) => void;
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  /** Normalized 0..1 audio energy from the analyser. */
  energyRef: React.MutableRefObject<number>;
  error: string | null;
}

const AudioContextReact = createContext<AudioState | null>(null);

const MUTE_KEY = "lb.muted";
const VOL_KEY = "lb.volume";

export function AudioProvider({ children }: { children: ReactNode }) {
  const { quietMode, pageVisible, windowFocused } = useExperience();

  const [consentGranted, setConsentGranted] = useState(false);
  const [muted, setMuted] = useState(false);
  const [volume, setVolumeState] = useState(0.8);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const audioElRef = useRef<HTMLAudioElement | null>(null);
  const ctxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const dataRef = useRef<Uint8Array<ArrayBuffer> | null>(null);
  const energyRef = useRef(0);
  const rafRef = useRef<number | null>(null);
  const loadedSrc = useRef<string | null>(null);

  // Persisted mute/volume.
  useEffect(() => {
    try {
      if (localStorage.getItem(MUTE_KEY) === "true") setMuted(true);
      const v = localStorage.getItem(VOL_KEY);
      if (v != null) setVolumeState(Math.min(1, Math.max(0, Number(v))));
    } catch {
      /* ignore */
    }
  }, []);

  const effectiveVolume = muted || quietMode ? 0 : volume;

  const ensureElement = useCallback(() => {
    if (audioElRef.current) return audioElRef.current;
    const el = new Audio();
    el.preload = "metadata";
    el.crossOrigin = "anonymous";
    el.addEventListener("timeupdate", () => setCurrentTime(el.currentTime));
    el.addEventListener("durationchange", () =>
      setDuration(Number.isFinite(el.duration) ? el.duration : 0),
    );
    el.addEventListener("ended", () => setIsPlaying(false));
    el.addEventListener("play", () => setIsPlaying(true));
    el.addEventListener("pause", () => setIsPlaying(false));
    el.addEventListener("error", () =>
      setError("Audio could not be loaded. A text interface remains available."),
    );
    audioElRef.current = el;
    return el;
  }, []);

  const ensureGraph = useCallback(() => {
    const el = ensureElement();
    if (ctxRef.current) return;
    try {
      const Ctx =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext })
          .webkitAudioContext;
      const ctx = new Ctx();
      const source = ctx.createMediaElementSource(el);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyser.connect(ctx.destination);
      ctxRef.current = ctx;
      analyserRef.current = analyser;
      dataRef.current = new Uint8Array(analyser.frequencyBinCount);
    } catch {
      // Analyser is optional; playback still works without it.
    }
  }, [ensureElement]);

  // Energy sampling loop (only while playing + visible).
  useEffect(() => {
    const tick = () => {
      const analyser = analyserRef.current;
      const data = dataRef.current;
      if (analyser && data) {
        analyser.getByteFrequencyData(data);
        let sum = 0;
        for (let i = 0; i < data.length; i++) sum += data[i];
        const avg = sum / data.length / 255;
        // Smooth toward the new value.
        energyRef.current += (avg - energyRef.current) * 0.2;
      }
      rafRef.current = requestAnimationFrame(tick);
    };
    if (isPlaying && pageVisible) {
      rafRef.current = requestAnimationFrame(tick);
    }
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      if (!isPlaying) energyRef.current = 0;
    };
  }, [isPlaying, pageVisible]);

  // Apply effective volume.
  useEffect(() => {
    const el = audioElRef.current;
    if (el) el.volume = effectiveVolume;
  }, [effectiveVolume]);

  const pause = useCallback(() => {
    audioElRef.current?.pause();
  }, []);

  // Pause when tab hidden, window blurred, or quiet mode (spec §7).
  useEffect(() => {
    if ((!pageVisible || !windowFocused || quietMode) && isPlaying) {
      pause();
    }
  }, [pageVisible, windowFocused, quietMode, isPlaying, pause]);

  const grantConsent = useCallback(() => {
    setConsentGranted(true);
    track("audio_consent_granted");
  }, []);

  const load = useCallback(
    (src: string) => {
      const el = ensureElement();
      if (loadedSrc.current === src) return;
      el.src = src;
      loadedSrc.current = src;
      setError(null);
    },
    [ensureElement],
  );

  const play = useCallback(async () => {
    // No autoplay: play() is only ever called from an explicit user gesture.
    setConsentGranted(true);
    ensureGraph();
    try {
      await ctxRef.current?.resume();
      const el = ensureElement();
      el.volume = effectiveVolume;
      await el.play();
    } catch {
      setError("Playback was blocked. Use the controls to try again.");
    }
  }, [effectiveVolume, ensureElement, ensureGraph]);

  const seek = useCallback((seconds: number) => {
    const el = audioElRef.current;
    if (!el) return;
    const d = Number.isFinite(el.duration) ? el.duration : 0;
    el.currentTime = Math.min(Math.max(0, seconds), d || seconds);
    setCurrentTime(el.currentTime);
  }, []);

  const toggleMute = useCallback(() => {
    setMuted((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(MUTE_KEY, String(next));
      } catch {
        /* ignore */
      }
      track("audio_muted", { muted: next });
      return next;
    });
  }, []);

  const setVolume = useCallback((v: number) => {
    const clamped = Math.min(1, Math.max(0, v));
    setVolumeState(clamped);
    try {
      localStorage.setItem(VOL_KEY, String(clamped));
    } catch {
      /* ignore */
    }
  }, []);

  const value = useMemo<AudioState>(
    () => ({
      consentGranted,
      grantConsent,
      muted,
      toggleMute,
      volume,
      setVolume,
      effectiveVolume,
      load,
      play,
      pause,
      seek,
      isPlaying,
      currentTime,
      duration,
      energyRef,
      error,
    }),
    [
      consentGranted,
      grantConsent,
      muted,
      toggleMute,
      volume,
      setVolume,
      effectiveVolume,
      load,
      play,
      pause,
      seek,
      isPlaying,
      currentTime,
      duration,
      error,
    ],
  );

  return (
    <AudioContextReact.Provider value={value}>
      {children}
    </AudioContextReact.Provider>
  );
}

export function useAudio(): AudioState {
  const ctx = useContext(AudioContextReact);
  if (!ctx) throw new Error("useAudio must be used within AudioProvider");
  return ctx;
}
