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
import {
  detectTier,
  nextLowerTier,
  prefersReducedMotion,
  type QualityTier,
} from "../lib/capability";
import { track } from "../lib/analytics";

interface Pointer {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

interface ExperienceState {
  reducedMotion: boolean;
  quietMode: boolean;
  toggleQuietMode: () => void;
  quality: QualityTier;
  downgradeQuality: () => void;
  pointer: React.MutableRefObject<Pointer>;
  pageVisible: boolean;
  windowFocused: boolean;
  /** True when decorative motion/WebGL should be suppressed entirely. */
  motionSuppressed: boolean;
}

const ExperienceContext = createContext<ExperienceState | null>(null);

const QUIET_KEY = "lb.quietMode";

export function ExperienceProvider({ children }: { children: ReactNode }) {
  const [reducedMotion, setReducedMotion] = useState(prefersReducedMotion);
  const [quietMode, setQuietMode] = useState(false);
  const [quality, setQuality] = useState<QualityTier>(detectTier);
  const [pageVisible, setPageVisible] = useState(true);
  const [windowFocused, setWindowFocused] = useState(true);
  const pointer = useRef<Pointer>({ x: 0.5, y: 0.5, vx: 0, vy: 0 });
  const lastMove = useRef<{ x: number; y: number; t: number }>({
    x: 0.5,
    y: 0.5,
    t: 0,
  });

  // Initial tier + persisted quiet mode (client-only).
  useEffect(() => {
    setQuality(detectTier());
    try {
      setQuietMode(localStorage.getItem(QUIET_KEY) === "true");
    } catch {
      /* ignore */
    }
  }, []);

  // Reduced-motion live updates.
  useEffect(() => {
    if (!window.matchMedia) return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const onChange = () => setReducedMotion(mq.matches);
    mq.addEventListener?.("change", onChange);
    return () => mq.removeEventListener?.("change", onChange);
  }, []);

  // Visibility + focus.
  useEffect(() => {
    const onVis = () => setPageVisible(!document.hidden);
    const onFocus = () => setWindowFocused(true);
    const onBlur = () => setWindowFocused(false);
    document.addEventListener("visibilitychange", onVis);
    window.addEventListener("focus", onFocus);
    window.addEventListener("blur", onBlur);
    return () => {
      document.removeEventListener("visibilitychange", onVis);
      window.removeEventListener("focus", onFocus);
      window.removeEventListener("blur", onBlur);
    };
  }, []);

  // Pointer position + velocity (stored in a ref to avoid re-renders).
  useEffect(() => {
    const onMove = (e: PointerEvent) => {
      const x = e.clientX / window.innerWidth;
      const y = e.clientY / window.innerHeight;
      const now = performance.now();
      const dt = Math.max(16, now - lastMove.current.t);
      pointer.current.vx = (x - lastMove.current.x) / (dt / 1000);
      pointer.current.vy = (y - lastMove.current.y) / (dt / 1000);
      pointer.current.x = x;
      pointer.current.y = y;
      lastMove.current = { x, y, t: now };
    };
    window.addEventListener("pointermove", onMove, { passive: true });
    return () => window.removeEventListener("pointermove", onMove);
  }, []);

  // Reflect quiet mode on <html> for CSS suppression.
  useEffect(() => {
    document.documentElement.classList.toggle("quiet-mode", quietMode);
  }, [quietMode]);

  const toggleQuietMode = useCallback(() => {
    setQuietMode((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(QUIET_KEY, String(next));
      } catch {
        /* ignore */
      }
      track("sensory_mode_changed", { quietMode: next });
      return next;
    });
  }, []);

  const downgradeQuality = useCallback(() => {
    setQuality((prev) => {
      const lower = nextLowerTier(prev);
      if (lower) {
        track("visual_quality_changed", { quality: lower, reason: "auto" });
        return lower;
      }
      return prev;
    });
  }, []);

  const motionSuppressed = reducedMotion || quietMode;

  const value = useMemo<ExperienceState>(
    () => ({
      reducedMotion,
      quietMode,
      toggleQuietMode,
      quality,
      downgradeQuality,
      pointer,
      pageVisible,
      windowFocused,
      motionSuppressed,
    }),
    [
      reducedMotion,
      quietMode,
      toggleQuietMode,
      quality,
      downgradeQuality,
      pageVisible,
      windowFocused,
      motionSuppressed,
    ],
  );

  return (
    <ExperienceContext.Provider value={value}>
      {children}
    </ExperienceContext.Provider>
  );
}

export function useExperience(): ExperienceState {
  const ctx = useContext(ExperienceContext);
  if (!ctx)
    throw new Error("useExperience must be used within ExperienceProvider");
  return ctx;
}
