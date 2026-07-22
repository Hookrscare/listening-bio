import { useMemo, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { useExperience } from "../../providers/ExperienceProvider";
import { useAudio } from "../../providers/AudioProvider";
import { TIER_BUDGETS, type QualityTier } from "../../lib/capability";

const vertexShader = /* glsl */ `
  uniform float uTime;
  uniform vec2 uPointer;
  uniform float uPointerVel;
  uniform float uEnergy;
  varying float vElevation;
  varying vec2 vUv;

  // Simplex-ish FBM noise (compact, texture-free).
  vec3 mod289(vec3 x){return x-floor(x*(1.0/289.0))*289.0;}
  vec4 mod289(vec4 x){return x-floor(x*(1.0/289.0))*289.0;}
  vec4 permute(vec4 x){return mod289(((x*34.0)+1.0)*x);}
  vec4 taylorInvSqrt(vec4 r){return 1.79284291400159-0.85373472095314*r;}
  float snoise(vec3 v){
    const vec2 C=vec2(1.0/6.0,1.0/3.0);const vec4 D=vec4(0.0,0.5,1.0,2.0);
    vec3 i=floor(v+dot(v,C.yyy));vec3 x0=v-i+dot(i,C.xxx);
    vec3 g=step(x0.yzx,x0.xyz);vec3 l=1.0-g;vec3 i1=min(g.xyz,l.zxy);vec3 i2=max(g.xyz,l.zxy);
    vec3 x1=x0-i1+C.xxx;vec3 x2=x0-i2+C.yyy;vec3 x3=x0-D.yyy;
    i=mod289(i);
    vec4 p=permute(permute(permute(i.z+vec4(0.0,i1.z,i2.z,1.0))+i.y+vec4(0.0,i1.y,i2.y,1.0))+i.x+vec4(0.0,i1.x,i2.x,1.0));
    float n_=0.142857142857;vec3 ns=n_*D.wyz-D.xzx;
    vec4 j=p-49.0*floor(p*ns.z*ns.z);
    vec4 x_=floor(j*ns.z);vec4 y_=floor(j-7.0*x_);
    vec4 x=x_*ns.x+ns.yyyy;vec4 y=y_*ns.x+ns.yyyy;vec4 h=1.0-abs(x)-abs(y);
    vec4 b0=vec4(x.xy,y.xy);vec4 b1=vec4(x.zw,y.zw);
    vec4 s0=floor(b0)*2.0+1.0;vec4 s1=floor(b1)*2.0+1.0;vec4 sh=-step(h,vec4(0.0));
    vec4 a0=b0.xzyw+s0.xzyw*sh.xxyy;vec4 a1=b1.xzyw+s1.xzyw*sh.zzww;
    vec3 p0=vec3(a0.xy,h.x);vec3 p1=vec3(a0.zw,h.y);vec3 p2=vec3(a1.xy,h.z);vec3 p3=vec3(a1.zw,h.w);
    vec4 norm=taylorInvSqrt(vec4(dot(p0,p0),dot(p1,p1),dot(p2,p2),dot(p3,p3)));
    p0*=norm.x;p1*=norm.y;p2*=norm.z;p3*=norm.w;
    vec4 m=max(0.6-vec4(dot(x0,x0),dot(x1,x1),dot(x2,x2),dot(x3,x3)),0.0);m=m*m;
    return 42.0*dot(m*m,vec4(dot(p0,x0),dot(p1,x1),dot(p2,x2),dot(p3,x3)));
  }
  float fbm(vec3 p){
    float f=0.0;float a=0.5;
    for(int i=0;i<4;i++){f+=a*snoise(p);p*=2.0;a*=0.5;}
    return f;
  }

  void main(){
    vUv=uv;
    vec3 pos=position;
    float breathe=sin(uTime*0.4)*0.15;
    float n=fbm(vec3(pos.x*0.5+uTime*0.06, pos.y*0.5, uTime*0.08));
    float pd=distance(uv, uPointer*0.5+0.25);
    float pointerLift=smoothstep(0.5,0.0,pd)*(0.35+uPointerVel*0.15);
    float elevation=n*(0.9+breathe)+pointerLift+uEnergy*0.6*n;
    pos.z+=elevation;
    vElevation=elevation;
    gl_Position=projectionMatrix*modelViewMatrix*vec4(pos,1.0);
  }
`;

const fragmentShader = /* glsl */ `
  uniform float uEnergy;
  varying float vElevation;
  varying vec2 vUv;
  void main(){
    vec3 deep=vec3(0.02,0.09,0.06);
    vec3 mint=vec3(0.28,0.85,0.6);
    vec3 lime=vec3(0.72,1.0,0.4);
    float t=clamp(vElevation*0.6+0.5,0.0,1.0);
    vec3 col=mix(deep,mint,t);
    col=mix(col,lime,smoothstep(0.7,1.1,vElevation)+uEnergy*0.25);
    // Fresnel-like edge glow using uv distance from center.
    float edge=smoothstep(0.2,0.75,distance(vUv,vec2(0.5)));
    float alpha=0.32+edge*0.4+smoothstep(0.6,1.1,vElevation)*0.3;
    gl_FragColor=vec4(col,alpha);
  }
`;

function LivingMembrane({ tier }: { tier: Exclude<QualityTier, "unsupported"> }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const matRef = useRef<THREE.ShaderMaterial>(null);
  const { pointer, motionSuppressed } = useExperience();
  const { energyRef } = useAudio();
  const seg = TIER_BUDGETS[tier].segments;

  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uPointer: { value: new THREE.Vector2(0.5, 0.5) },
      uPointerVel: { value: 0 },
      uEnergy: { value: 0 },
    }),
    [],
  );

  useFrame((_, delta) => {
    const m = matRef.current;
    if (!m) return;
    if (!motionSuppressed) {
      m.uniforms.uTime.value += delta;
    }
    const vel = Math.min(
      2,
      Math.hypot(pointer.current.vx, pointer.current.vy),
    );
    // Smoothly follow pointer; subtle response only.
    const up = m.uniforms.uPointer.value as THREE.Vector2;
    up.x += (pointer.current.x - up.x) * 0.05;
    up.y += (1 - pointer.current.y - up.y) * 0.05;
    m.uniforms.uPointerVel.value +=
      (vel - m.uniforms.uPointerVel.value) * 0.1;
    // Audio energy affects displacement/glow only (never the camera).
    m.uniforms.uEnergy.value +=
      (energyRef.current - m.uniforms.uEnergy.value) * 0.1;
  });

  return (
    <mesh ref={meshRef} rotation={[-Math.PI / 2.4, 0, 0]} position={[0, -0.3, 0]}>
      <planeGeometry args={[8, 6, seg, seg]} />
      <shaderMaterial
        ref={matRef}
        uniforms={uniforms}
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        transparent
        blending={THREE.AdditiveBlending}
        depthWrite={false}
        side={THREE.DoubleSide}
      />
    </mesh>
  );
}

function AtmosphericField({
  tier,
}: {
  tier: Exclude<QualityTier, "unsupported">;
}) {
  const count = TIER_BUDGETS[tier].particles;
  const pointsRef = useRef<THREE.Points>(null);
  const { motionSuppressed } = useExperience();

  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      arr[i * 3] = (Math.random() - 0.5) * 9;
      arr[i * 3 + 1] = Math.random() * 3.5 - 0.5;
      arr[i * 3 + 2] = (Math.random() - 0.5) * 6;
    }
    return arr;
  }, [count]);

  useFrame((_, delta) => {
    if (motionSuppressed || !pointsRef.current) return;
    pointsRef.current.rotation.y += delta * 0.02;
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.03}
        color={"#9fffcf"}
        transparent
        opacity={0.5}
        sizeAttenuation
        depthWrite={false}
      />
    </points>
  );
}

function CameraRig() {
  const { pointer, motionSuppressed } = useExperience();
  const { camera } = useThree();
  useFrame(() => {
    if (motionSuppressed) return;
    // Subtle pointer-linked camera drift — never large movement (spec §3).
    const tx = (pointer.current.x - 0.5) * 0.6;
    const ty = -(pointer.current.y - 0.5) * 0.35;
    camera.position.x += (tx - camera.position.x) * 0.03;
    camera.position.y += (0.8 + ty - camera.position.y) * 0.03;
    camera.lookAt(0, 0, 0);
  });
  return null;
}

// Auto-downgrade controller: samples FPS and drops a tier if sustained low.
function PerformanceController() {
  const { downgradeQuality } = useExperience();
  const frames = useRef<number[]>([]);
  const decided = useRef(false);
  useFrame((_, delta) => {
    if (decided.current) return;
    const fps = 1 / delta;
    frames.current.push(fps);
    if (frames.current.length >= 90) {
      const avg =
        frames.current.reduce((a, b) => a + b, 0) / frames.current.length;
      frames.current = [];
      if (avg < 34) {
        decided.current = true;
        downgradeQuality();
      } else if (avg < 48) {
        decided.current = true;
        downgradeQuality();
      }
    }
  });
  return null;
}

export function HeroScene({
  tier,
}: {
  tier: Exclude<QualityTier, "unsupported">;
}) {
  return (
    <>
      <ambientLight intensity={0.6} />
      <pointLight position={[2, 3, 2]} intensity={1.2} color={"#b7ff65"} />
      <pointLight position={[-3, 1, -2]} intensity={0.6} color={"#72f2c7"} />
      <fog attach="fog" args={["#030706", 5, 12]} />
      <LivingMembrane tier={tier} />
      <AtmosphericField tier={tier} />
      <CameraRig />
      <PerformanceController />
    </>
  );
}
