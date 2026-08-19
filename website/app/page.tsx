"use client";

import { useEffect, useRef } from "react";

const budget = [
  ["Recording equipment", "$2,000"],
  ["Field collection", "$2,000"],
  ["Scientific review", "$2,500"],
  ["Engineering + data", "$2,000"],
  ["Reporting + workshop", "$1,000"],
  ["Contingency", "$500"],
];

function SignalField() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext("2d");
    if (!context) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let pointerX = 0.5;
    let pointerY = 0.5;
    let frame = 0;

    const resize = () => {
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      if (width <= 0 || height <= 0) return;
      canvas.width = width * ratio;
      canvas.height = height * ratio;
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
    };
    const move = (event: PointerEvent) => {
      const rect = canvas.getBoundingClientRect();
      pointerX = (event.clientX - rect.left) / rect.width;
      pointerY = (event.clientY - rect.top) / rect.height;
    };
    const draw = (time: number) => {
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      context.clearRect(0, 0, width, height);
      const t = reduced ? 0 : time * 0.00025;
      context.save();
      context.translate((pointerX - 0.5) * 18, (pointerY - 0.5) * 12);

      for (let band = 0; band < 22; band += 1) {
        context.beginPath();
        const base = height * (0.24 + band * 0.025);
        for (let x = -40; x <= width + 40; x += 8) {
          const envelope = Math.sin((x / width) * Math.PI);
          const y = base + Math.sin(x * 0.012 + t * (1 + band * 0.05) + band * 0.31) * (18 + band * 1.6) * envelope;
          if (x === -40) context.moveTo(x, y);
          else context.lineTo(x, y);
        }
        context.strokeStyle = band % 4 === 0 ? `rgba(183,255,101,${0.13 + band * 0.004})` : `rgba(114,242,199,${0.055 + band * 0.002})`;
        context.lineWidth = band % 4 === 0 ? 1.2 : 0.7;
        context.stroke();
      }

      for (let i = 0; i < 38; i += 1) {
        const x = ((i * 79.3 + t * 32) % (width + 120)) - 60;
        const y = height * (0.2 + ((i * 47) % 66) / 100);
        const pulse = 1 + Math.sin(t * 4 + i) * 0.4;
        context.beginPath();
        context.arc(x, y, (i % 5 === 0 ? 3 : 1.3) * pulse, 0, Math.PI * 2);
        context.fillStyle = i % 5 === 0 ? "rgba(183,255,101,.65)" : "rgba(208,255,239,.32)";
        context.fill();
      }
      context.restore();
      frame = requestAnimationFrame(draw);
    };

    resize();
    window.addEventListener("resize", resize);
    canvas.addEventListener("pointermove", move);
    frame = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", resize);
      canvas.removeEventListener("pointermove", move);
    };
  }, []);

  return <canvas ref={canvasRef} className="signal-field" aria-hidden="true" />;
}

export default function Home() {
  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="Listening.bio home">
          <span className="brand-signal" aria-hidden="true"><i /><i /><i /><i /><i /></span>
          <strong>listening<span>.bio</span></strong>
        </a>
        <nav aria-label="Primary navigation">
          <a href="#pilot">Pilot</a>
          <a href="#method">Method</a>
          <a href="#partners">Partners</a>
        </nav>
        <a className="header-action" href="mailto:rodrigo@listening.bio?subject=Listening.bio%20pilot%20partnership">Discuss a pilot</a>
      </header>

      <section className="hero" id="top">
        <SignalField />
        <div className="hero-grid" aria-hidden="true" />
        <div className="hero-copy">
          <p className="eyebrow">Auditable acoustic biodiversity monitoring</p>
          <h1>Nature leaves<br />a signal.</h1>
          <p className="hero-deck">Listening.bio turns environmental sound into transparent, reviewable evidence for the places that need protection.</p>
          <div className="hero-actions">
            <a className="primary" href="mailto:rodrigo@listening.bio?subject=Listening.bio%20pilot%20partnership">Become a pilot partner <span>↗</span></a>
            <a className="secondary" href="#pilot">Explore the pilot <span>↓</span></a>
          </div>
        </div>
        <div className="hero-index">
          <span>FIELD / NYC 01</span>
          <span>40.7829 N</span>
          <span>73.9654 W</span>
        </div>
        <div className="principle"><span>Our principle</span><strong>Automated detections are evidence candidates, not final ecological truth.</strong></div>
      </section>

      <section className="proof" aria-label="Current readiness">
        <article><span>01 / Workflow</span><strong>Functional MVP</strong><p>Audio, BirdNET, provenance, review, maps, and exports.</p></article>
        <article><span>02 / Evidence</span><strong>Real audio tested</strong><p>A public environmental recording completed the full pipeline.</p></article>
        <article><span>03 / Next proof</span><strong>Partner-led field pilot</strong><p>Scientifically reviewed evidence from approved local sites.</p></article>
      </section>

      <section className="statement" id="method">
        <p className="eyebrow">Why this exists</p>
        <h2>Listen longer.<br />Claim less.<br /><em>Learn more.</em></h2>
        <div className="statement-copy"><p>Acoustic monitoring can extend observation across more hours and locations than point-in-time surveys. But automated predictions become misleading when the source, settings, confidence, and review decisions disappear.</p><p>Listening.bio keeps the evidence chain intact, from the original WAV recording to every human decision.</p></div>
      </section>

      <section className="pilot" id="pilot">
        <div className="section-head"><div><p className="eyebrow">Proposed collaboration</p><h2>A focused<br />$10,000 pilot.</h2></div><p>Thirty days across three to five urban green-space sites, designed with a qualified scientific collaborator and an eligible lead partner.</p></div>
        <div className="pilot-measures">
          <article><strong>30</strong><span>days</span></article>
          <article><strong>3–5</strong><span>sites</span></article>
          <article><strong>50–100</strong><span>WAV recordings</span></article>
          <article><strong>1</strong><span>reviewed dataset</span></article>
        </div>
        <div className="workflow" aria-label="Pilot workflow">
          {[["01","Collect","Standardized field audio"],["02","Process","Documented BirdNET run"],["03","Preserve","Source and model provenance"],["04","Review","Qualified human validation"],["05","Report","Conservative findings"]].map(([n,title,copy]) => <article key={n}><span>{n}</span><div><strong>{title}</strong><p>{copy}</p></div></article>)}
        </div>
      </section>

      <section className="partners" id="partners">
        <div className="section-head"><div><p className="eyebrow">The collaboration model</p><h2>One pilot.<br />Four roles.</h2></div><p>Listening.bio is enabling infrastructure. Scientific interpretation and site decisions stay with qualified partners.</p></div>
        <div className="partner-grid">
          <article><span>Lead applicant</span><h3>Eligible organization</h3><p>A university, nonprofit, public agency, land trust, or fiscal sponsor manages the award.</p></article>
          <article><span>Scientific lead</span><h3>Ecological reviewer</h3><p>An ecologist, ornithologist, or bioacoustics researcher approves protocol and validation.</p></article>
          <article><span>Site partner</span><h3>Landscape steward</h3><p>A park or land manager supports access and defines the questions that matter.</p></article>
          <article><span>Technology partner</span><h3>Listening.bio</h3><p>We provide processing, provenance, review tools, structured exports, and reporting support.</p></article>
        </div>
      </section>

      <section className="budget">
        <div><p className="eyebrow">Transparent by design</p><h2>Where the pilot<br />funding goes.</h2><p className="budget-note">A deliberately small budget focused on field evidence, scientific quality, and reusable outputs.</p></div>
        <div className="budget-list">{budget.map(([label,amount]) => <div key={label}><span>{label}</span><strong>{amount}</strong></div>)}<div className="total"><span>Total requested</span><strong>$10,000</strong></div></div>
      </section>

      <section className="boundary">
        <p className="eyebrow">Evidence boundary</p>
        <h2>What we will not claim.</h2>
        <div className="boundary-grid"><p>Automated predictions are not confirmed observations.</p><p>A pilot is not comprehensive biodiversity coverage.</p><p>Acoustic monitoring does not replace expert ecological surveys.</p><p>Sensitive locations will not be published without review.</p></div>
      </section>

      <section className="closing">
        <SignalField />
        <div><p className="eyebrow">Pilot partnerships / 2026</p><h2>What could your<br />landscape tell you?</h2><p>We are looking for one lead applicant, one scientific collaborator, and one site partner ready to build credible field evidence together.</p><a className="primary" href="mailto:rodrigo@listening.bio?subject=Listening.bio%20pilot%20partnership">Start the conversation <span>↗</span></a></div>
      </section>

      <footer><div className="brand"><span className="brand-signal" aria-hidden="true"><i /><i /><i /><i /><i /></span><strong>listening<span>.bio</span></strong></div><p>Biodiversity, heard.</p><a href="mailto:rodrigo@listening.bio">rodrigo@listening.bio</a><span>© 2026 Listening.bio</span></footer>
    </main>
  );
}
