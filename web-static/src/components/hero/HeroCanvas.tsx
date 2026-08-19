import { Component, useState, type ReactNode } from "react";
import { Canvas } from "@react-three/fiber";
import { TIER_BUDGETS, type QualityTier } from "../../lib/capability";
import { useExperience } from "../../providers/ExperienceProvider";
import { HeroScene } from "./HeroScene";

class WebGLErrorBoundary extends Component<
  { fallback: ReactNode; children: ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  render() {
    if (this.state.hasError) return this.props.fallback;
    return this.props.children;
  }
}

function HeroCanvasInner({ fallback }: { fallback: ReactNode }) {
  const { quality, pageVisible, windowFocused, motionSuppressed } =
    useExperience();
  const [contextLost, setContextLost] = useState(false);

  if (quality === "unsupported" || motionSuppressed || contextLost) {
    return <>{fallback}</>;
  }

  const tier = quality as Exclude<QualityTier, "unsupported">;
  const dpr = Math.min(window.devicePixelRatio || 1, TIER_BUDGETS[tier].dprCeiling);

  return (
    <WebGLErrorBoundary fallback={fallback}>
      <Canvas
        className="hero-canvas"
        aria-hidden="true"
        dpr={dpr}
        camera={{ position: [0, 0.8, 5], fov: 50 }}
        gl={{ antialias: tier === "high", powerPreference: "high-performance" }}
        // Pause the render loop when hidden/blurred (spec §11).
        frameloop={pageVisible && windowFocused ? "always" : "never"}
        onCreated={({ gl }) => {
          const domElem = gl.domElement;
          if (domElem) {
            domElem.addEventListener("webglcontextlost", (e) => {
              e.preventDefault();
              setContextLost(true);
            }, { once: true });
          }
        }}
      >
        <HeroScene tier={tier} />
      </Canvas>
    </WebGLErrorBoundary>
  );
}

// Default export so it can be lazy-loaded (keeps three.js out of the initial chunk).
export default function HeroCanvas({ fallback }: { fallback: ReactNode }) {
  return <HeroCanvasInner fallback={fallback} />;
}
