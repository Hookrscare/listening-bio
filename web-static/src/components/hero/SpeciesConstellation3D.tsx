import { useRef, useState, useMemo, Component, type ReactNode } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { playBioacousticSound } from "../../lib/bioacousticSynth";
import { useExperience } from "../../providers/ExperienceProvider";

interface ConstellationNode {
  id: string;
  presetId: string;
  name: string;
  scientificName: string;
  confidence: number;
  freq: string;
  pos: [number, number, number];
  color: string;
}

const NODES: ConstellationNode[] = [
  {
    id: "node-1",
    presetId: "robin",
    name: "American Robin",
    scientificName: "Turdus migratorius",
    confidence: 0.94,
    freq: "2.4 kHz",
    pos: [1.8, 0.6, 0.4],
    color: "#b7ff65",
  },
  {
    id: "node-2",
    presetId: "cardinal",
    name: "Northern Cardinal",
    scientificName: "Cardinalis cardinalis",
    confidence: 0.88,
    freq: "3.2 kHz",
    pos: [-1.6, 0.8, -0.6],
    color: "#72f2c7",
  },
  {
    id: "node-3",
    presetId: "thrush",
    name: "Wood Thrush",
    scientificName: "Hylocichla mustelina",
    confidence: 0.91,
    freq: "3.8 kHz",
    pos: [0.4, 1.4, -1.2],
    color: "#38bdf8",
  },
  {
    id: "node-4",
    presetId: "owl",
    name: "Great Horned Owl",
    scientificName: "Bubo virginianus",
    confidence: 0.85,
    freq: "320 Hz",
    pos: [-1.2, -0.9, 0.8],
    color: "#ffcf6b",
  },
  {
    id: "node-5",
    presetId: "chorus",
    name: "Dawn Biophony Hub",
    scientificName: "Acoustic Biodiversity Cluster",
    confidence: 0.97,
    freq: "Wideband",
    pos: [0, 0, 0],
    color: "#b7ff65",
  },
];

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

function OrbitingCluster({
  activeNode,
  setActiveNode,
  onPlaySound,
}: {
  activeNode: ConstellationNode | null;
  setActiveNode: (n: ConstellationNode | null) => void;
  onPlaySound: (n: ConstellationNode) => void;
}) {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.15;
    }
  });

  const linePositions = useMemo(() => {
    const points: number[] = [];
    for (let i = 0; i < NODES.length; i++) {
      for (let j = i + 1; j < NODES.length; j++) {
        points.push(...NODES[i].pos);
        points.push(...NODES[j].pos);
      }
    }
    return new Float32Array(points);
  }, []);

  return (
    <group ref={groupRef}>
      {/* Dynamic line connections */}
      <lineSegments>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={linePositions.length / 3}
            array={linePositions}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial color="#72f2c7" transparent opacity={0.22} />
      </lineSegments>

      {/* Orbit Rings */}
      <mesh rotation={[Math.PI / 2.8, 0, 0]}>
        <ringGeometry args={[2.1, 2.12, 64]} />
        <meshBasicMaterial color="#b7ff65" transparent opacity={0.25} side={THREE.DoubleSide} />
      </mesh>
      <mesh rotation={[-Math.PI / 3.2, Math.PI / 6, 0]}>
        <ringGeometry args={[1.5, 1.515, 64]} />
        <meshBasicMaterial color="#72f2c7" transparent opacity={0.2} side={THREE.DoubleSide} />
      </mesh>

      {/* Interactive Species Nodes */}
      {NODES.map((node) => {
        const isSelected = activeNode?.id === node.id;
        return (
          <group
            key={node.id}
            position={node.pos}
            onPointerOver={(e) => {
              e.stopPropagation();
              setActiveNode(node);
            }}
            onClick={(e) => {
              e.stopPropagation();
              setActiveNode(node);
              onPlaySound(node);
            }}
          >
            <mesh>
              <sphereGeometry args={[isSelected ? 0.18 : 0.11, 24, 24]} />
              <meshStandardMaterial
                color={node.color}
                emissive={node.color}
                emissiveIntensity={isSelected ? 1.8 : 0.6}
                roughness={0.2}
              />
            </mesh>
            {/* Halo ring */}
            <mesh rotation={[Math.PI / 2, 0, 0]}>
              <ringGeometry args={[0.22, 0.25, 32]} />
              <meshBasicMaterial
                color={node.color}
                transparent
                opacity={isSelected ? 0.9 : 0.3}
                side={THREE.DoubleSide}
              />
            </mesh>
          </group>
        );
      })}
    </group>
  );
}

function Fallback2D({
  activeNode,
  setActiveNode,
  onPlaySound,
}: {
  activeNode: ConstellationNode | null;
  setActiveNode: (n: ConstellationNode | null) => void;
  onPlaySound: (n: ConstellationNode) => void;
}) {
  return (
    <svg viewBox="0 0 400 240" className="constellation-fallback-svg" aria-hidden="true">
      <defs>
        <radialGradient id="nodeGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#b7ff65" stopOpacity="0.8" />
          <stop offset="100%" stopColor="#72f2c7" stopOpacity="0" />
        </radialGradient>
      </defs>
      {/* Background connection lines */}
      <line x1="120" y1="60" x2="280" y2="70" stroke="rgba(114,242,199,0.3)" strokeWidth="1" />
      <line x1="120" y1="60" x2="200" y2="140" stroke="rgba(114,242,199,0.3)" strokeWidth="1" />
      <line x1="280" y1="70" x2="200" y2="140" stroke="rgba(114,242,199,0.3)" strokeWidth="1" />
      <line x1="200" y1="140" x2="160" y2="190" stroke="rgba(114,242,199,0.3)" strokeWidth="1" />
      <line x1="200" y1="140" x2="310" y2="170" stroke="rgba(114,242,199,0.3)" strokeWidth="1" />

      {NODES.map((node, i) => {
        const coords = [
          [200, 140],
          [120, 60],
          [280, 70],
          [160, 190],
          [310, 170],
        ][i] || [200, 140];
        const isSelected = activeNode?.id === node.id;

        return (
          <g
            key={node.id}
            onClick={() => {
              setActiveNode(node);
              onPlaySound(node);
            }}
            style={{ cursor: "pointer" }}
          >
            <circle cx={coords[0]} cy={coords[1]} r={isSelected ? 14 : 9} fill={node.color} opacity={isSelected ? 0.95 : 0.75} />
            <circle cx={coords[0]} cy={coords[1]} r={isSelected ? 22 : 15} stroke={node.color} strokeWidth="1" fill="none" opacity={0.4} />
          </g>
        );
      })}
    </svg>
  );
}

export function SpeciesConstellation3D() {
  const [activeNode, setActiveNode] = useState<ConstellationNode | null>(NODES[0]);
  const [playing, setPlaying] = useState<string | null>(null);
  const { quality, motionSuppressed } = useExperience();

  const handlePlaySound = (node: ConstellationNode) => {
    setPlaying(node.name);
    playBioacousticSound(node.presetId);
    setTimeout(() => {
      setPlaying(null);
    }, 2000);
  };

  const is3DAvailable = quality !== "unsupported" && !motionSuppressed;

  const fallback = (
    <Fallback2D
      activeNode={activeNode}
      setActiveNode={setActiveNode}
      onPlaySound={handlePlaySound}
    />
  );

  return (
    <div className="constellation-3d-wrapper" aria-label="Interactive 3D bioacoustic species constellation">
      <div className="canvas-container">
        {is3DAvailable ? (
          <WebGLErrorBoundary fallback={fallback}>
            <Canvas camera={{ position: [0, 1.2, 4.2], fov: 48 }}>
              <ambientLight intensity={0.7} />
              <pointLight position={[3, 4, 3]} intensity={1.5} color="#b7ff65" />
              <pointLight position={[-3, -2, -2]} intensity={0.8} color="#72f2c7" />
              <OrbitingCluster
                activeNode={activeNode}
                setActiveNode={setActiveNode}
                onPlaySound={handlePlaySound}
              />
            </Canvas>
          </WebGLErrorBoundary>
        ) : (
          fallback
        )}
      </div>

      <div className="constellation-overlay">
        <div className="hud-badge">
          <span className="live-dot" />
          <span>INTERACTIVE DEMONSTRATION TOPOLOGY</span>
        </div>

        {activeNode && (
          <div className="active-species-card">
            <div className="card-top">
              <div>
                <span className="species-tag">{activeNode.freq} BAND</span>
                <h4>{activeNode.name}</h4>
                <p className="sci-name"><em>{activeNode.scientificName}</em></p>
              </div>
              <div className="confidence-pill">
                <strong>{Math.round(activeNode.confidence * 100)}%</strong>
                <span>Score</span>
              </div>
            </div>

            <div className="card-actions">
              <button
                type="button"
                className="play-node-btn"
                onClick={() => handlePlaySound(activeNode)}
              >
                {playing === activeNode.name ? "▶ Synthesizing pattern..." : "▶ Play synthesized pattern"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
