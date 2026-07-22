import { useEffect, useRef } from "react";
import { useExperience } from "../../providers/ExperienceProvider";

// 2D canvas fallback — ported from the vinext website/app/page.tsx SignalField.
// Used for reduced-motion, quiet mode, no-WebGL, and the minimal tier. Fully
// decorative (aria-hidden); no essential content lives here.
export function SignalField() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { motionSuppressed, pointer } = useExperience();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext("2d");
    if (!context) return;
    let frame = 0;

    const resize = () => {
      const ratio = Math.min(window.devicePixelRatio, 2);
      canvas.width = canvas.clientWidth * ratio;
      canvas.height = canvas.clientHeight * ratio;
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
    };

    const draw = (time: number) => {
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      context.clearRect(0, 0, width, height);
      const t = motionSuppressed ? 0 : time * 0.00025;
      const px = pointer.current.x;
      const py = pointer.current.y;
      context.save();
      context.translate((px - 0.5) * 18, (py - 0.5) * 12);

      for (let band = 0; band < 22; band += 1) {
        context.beginPath();
        const base = height * (0.24 + band * 0.025);
        for (let x = -40; x <= width + 40; x += 8) {
          const envelope = Math.sin((x / width) * Math.PI);
          const y =
            base +
            Math.sin(x * 0.012 + t * (1 + band * 0.05) + band * 0.31) *
              (18 + band * 1.6) *
              envelope;
          if (x === -40) context.moveTo(x, y);
          else context.lineTo(x, y);
        }
        context.strokeStyle =
          band % 4 === 0
            ? `rgba(183,255,101,${0.13 + band * 0.004})`
            : `rgba(114,242,199,${0.055 + band * 0.002})`;
        context.lineWidth = band % 4 === 0 ? 1.2 : 0.7;
        context.stroke();
      }

      if (!motionSuppressed) {
        for (let i = 0; i < 38; i += 1) {
          const x = ((i * 79.3 + t * 32) % (width + 120)) - 60;
          const y = height * (0.2 + ((i * 47) % 66) / 100);
          const pulse = 1 + Math.sin(t * 4 + i) * 0.4;
          context.beginPath();
          context.arc(x, y, (i % 5 === 0 ? 3 : 1.3) * pulse, 0, Math.PI * 2);
          context.fillStyle =
            i % 5 === 0 ? "rgba(183,255,101,.65)" : "rgba(208,255,239,.32)";
          context.fill();
        }
      }
      context.restore();

      if (!motionSuppressed) {
        frame = requestAnimationFrame(draw);
      }
    };

    resize();
    window.addEventListener("resize", resize);
    frame = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", resize);
    };
  }, [motionSuppressed, pointer]);

  return <canvas ref={canvasRef} className="signal-field" aria-hidden="true" />;
}
