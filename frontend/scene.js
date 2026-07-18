import * as THREE from "https://unpkg.com/three@0.170.0/build/three.module.js";

const canvas = document.querySelector("#biosphereCanvas");
const host = document.querySelector(".acoustic-visual");
const loader = document.querySelector("#sceneLoader");
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

if (canvas && host && window.WebGLRenderingContext) {
  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x030706, 0.038);

  const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
  camera.position.set(0, 0.55, 8.6);

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.38;

  const root = new THREE.Group();
  scene.add(root);

  const habitatGeometry = new THREE.IcosahedronGeometry(2.35, 5);
  const habitatMaterial = new THREE.ShaderMaterial({
    transparent: true,
    side: THREE.DoubleSide,
    uniforms: {
      uTime: { value: 0 },
      uPointer: { value: new THREE.Vector2() },
      uColorA: { value: new THREE.Color(0x72f2c7) },
      uColorB: { value: new THREE.Color(0xb7ff65) },
    },
    vertexShader: `
      uniform float uTime;
      uniform vec2 uPointer;
      varying vec3 vNormal;
      varying vec3 vPosition;
      void main() {
        vNormal = normalize(normalMatrix * normal);
        float signal = sin(position.y * 4.2 + uTime * 0.8) * 0.055;
        signal += sin(position.x * 7.0 - uTime * 0.45) * 0.025;
        signal += sin(length(position.xy) * 12.0 - uTime * 1.25) * 0.018;
        vec3 displaced = position + normal * signal;
        displaced.x += uPointer.x * 0.08 * (position.z + 2.0);
        displaced.y += uPointer.y * 0.05 * (position.z + 2.0);
        vPosition = displaced;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(displaced, 1.0);
      }
    `,
    fragmentShader: `
      uniform float uTime;
      uniform vec3 uColorA;
      uniform vec3 uColorB;
      varying vec3 vNormal;
      varying vec3 vPosition;
      void main() {
        float rim = pow(1.0 - abs(dot(vNormal, vec3(0.0, 0.0, 1.0))), 2.4);
        float bands = smoothstep(0.42, 0.58, sin(vPosition.y * 8.0 + uTime) * 0.5 + 0.5);
        float scan = pow(max(0.0, sin(vPosition.y * 18.0 - uTime * 1.4)), 9.0);
        vec3 color = mix(uColorA, uColorB, bands * 0.32 + rim * 0.28);
        color += scan * uColorB * 0.32;
        float alpha = 0.12 + rim * 0.72 + bands * 0.07 + scan * 0.18;
        gl_FragColor = vec4(color, alpha);
      }
    `,
  });
  const habitat = new THREE.Mesh(habitatGeometry, habitatMaterial);
  habitat.scale.set(1.65, 0.95, 1.08);
  habitat.rotation.z = -0.18;
  root.add(habitat);

  const wire = new THREE.LineSegments(
    new THREE.WireframeGeometry(new THREE.IcosahedronGeometry(2.42, 2)),
    new THREE.LineBasicMaterial({ color: 0xb7ff65, transparent: true, opacity: 0.2 }),
  );
  wire.scale.copy(habitat.scale);
  wire.rotation.copy(habitat.rotation);
  root.add(wire);

  const eventGeometry = new THREE.SphereGeometry(0.09, 16, 16);
  const events = new THREE.Group();
  for (let i = 0; i < 18; i += 1) {
    const material = new THREE.MeshBasicMaterial({
      color: i % 5 === 0 ? 0xb7ff65 : 0x72f2c7,
      transparent: true,
      opacity: 0.45 + (i % 4) * 0.12,
    });
    const point = new THREE.Mesh(eventGeometry, material);
    const angle = i * 2.399;
    const radius = 1.0 + (i % 6) * 0.27;
    point.position.set(Math.cos(angle) * radius * 1.35, Math.sin(angle) * radius * 0.72, Math.sin(i * 1.7) * 0.95);
    point.userData.phase = i * 0.45;
    events.add(point);
  }
  root.add(events);

  const ringMaterial = new THREE.MeshBasicMaterial({ color: 0x72f2c7, transparent: true, opacity: 0.16, side: THREE.DoubleSide });
  const rings = new THREE.Group();
  for (let i = 0; i < 5; i += 1) {
    const ring = new THREE.Mesh(new THREE.RingGeometry(1.2 + i * 0.48, 1.215 + i * 0.48, 96), ringMaterial.clone());
    ring.scale.y = 0.55;
    ring.position.z = -0.35 - i * 0.08;
    rings.add(ring);
  }
  root.add(rings);

  const dustPositions = new Float32Array(420 * 3);
  for (let i = 0; i < 420; i += 1) {
    const radius = 2.8 + Math.random() * 4.8;
    const angle = Math.random() * Math.PI * 2;
    dustPositions[i * 3] = Math.cos(angle) * radius;
    dustPositions[i * 3 + 1] = (Math.random() - 0.5) * 6.2;
    dustPositions[i * 3 + 2] = Math.sin(angle) * radius - 1.5;
  }
  const dustGeometry = new THREE.BufferGeometry();
  dustGeometry.setAttribute("position", new THREE.BufferAttribute(dustPositions, 3));
  const dust = new THREE.Points(dustGeometry, new THREE.PointsMaterial({ color: 0xb7ff65, size: 0.018, transparent: true, opacity: 0.34 }));
  scene.add(dust);

  const pointer = new THREE.Vector2();
  const targetPointer = new THREE.Vector2();
  host.addEventListener("pointermove", (event) => {
    const rect = host.getBoundingClientRect();
    targetPointer.set(((event.clientX - rect.left) / rect.width) * 2 - 1, -(((event.clientY - rect.top) / rect.height) * 2 - 1));
  }, { passive: true });
  host.addEventListener("pointerleave", () => targetPointer.set(0, 0), { passive: true });

  function resize() {
    const rect = host.getBoundingClientRect();
    renderer.setSize(rect.width, rect.height, false);
    camera.aspect = rect.width / Math.max(rect.height, 1);
    camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(host);
  resize();

  const clock = new THREE.Clock();
  function frame() {
    const elapsed = clock.getElapsedTime();
    pointer.lerp(targetPointer, reducedMotion ? 0.04 : 0.075);
    habitatMaterial.uniforms.uTime.value = reducedMotion ? 0 : elapsed;
    habitatMaterial.uniforms.uPointer.value.copy(pointer);

    const rect = host.getBoundingClientRect();
    const progress = THREE.MathUtils.clamp(-rect.top / Math.max(rect.height, 1), 0, 1);
    camera.position.x = pointer.x * 0.58 + progress * 0.95;
    camera.position.y = 0.55 + pointer.y * 0.34 - progress * 0.5;
    camera.position.z = 8.6 - progress * 1.4;
    camera.lookAt(0, 0, 0);

    if (!reducedMotion) {
      root.rotation.y = elapsed * 0.035 + pointer.x * 0.1;
      root.rotation.x = pointer.y * 0.05;
      dust.rotation.y = elapsed * 0.007;
      events.children.forEach((point) => {
        const pulse = 1 + Math.sin(elapsed * 1.7 + point.userData.phase) * 0.35;
        point.scale.setScalar(pulse);
      });
      rings.children.forEach((ring, index) => {
        ring.material.opacity = 0.07 + (Math.sin(elapsed * 0.8 - index * 0.6) * 0.5 + 0.5) * 0.12;
      });
    }

    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  window.setTimeout(() => {
    host.classList.add("scene-ready");
    loader?.setAttribute("aria-hidden", "true");
  }, reducedMotion ? 0 : 700);
} else {
  host?.classList.add("scene-fallback");
  if (loader) loader.textContent = "Static acoustic field";
}
