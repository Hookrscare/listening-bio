import { useEffect, useRef, useState } from "react";

export interface ChapterProgress {
  activeIndex: number;
  direction: "up" | "down";
}

// Tracks which narrative chapter is active using IntersectionObserver — native
// scrolling only, no scroll-jacking (spec §25).
export function useNarrativeState(count: number): ChapterProgress {
  const [activeIndex, setActiveIndex] = useState(0);
  const [direction, setDirection] = useState<"up" | "down">("down");
  const lastY = useRef(0);

  useEffect(() => {
    const onScroll = () => {
      const y = window.scrollY;
      setDirection(y >= lastY.current ? "down" : "up");
      lastY.current = y;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const els = Array.from(
      document.querySelectorAll<HTMLElement>("[data-chapter-index]"),
    );
    if (!els.length || typeof IntersectionObserver === "undefined") return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const idx = Number(
              (entry.target as HTMLElement).dataset.chapterIndex,
            );
            setActiveIndex(idx);
          }
        });
      },
      { threshold: 0.5 },
    );
    els.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, [count]);

  return { activeIndex, direction };
}
