import { ExperienceProvider } from "./providers/ExperienceProvider";
import { AudioProvider } from "./providers/AudioProvider";
import { Header } from "./components/layout/Header";
import { Footer } from "./components/layout/Footer";
import { Hero } from "./components/hero/Hero";
import { Narrative } from "./components/narrative/Narrative";
import { EvidenceDemo } from "./components/evidence/EvidenceDemo";
import { InteractiveSoundboard } from "./components/evidence/InteractiveSoundboard";
import { SpeciesConstellation3D } from "./components/hero/SpeciesConstellation3D";
import { RoiCalculator } from "./components/sections/RoiCalculator";
import { EnterpriseGovernance } from "./components/sections/EnterpriseGovernance";
import {
  Boundary,
  Budget,
  Closing,
  Partners,
  Pilot,
  Proof,
  Statement,
} from "./components/sections/ContentSections";
import { Contact } from "./components/sections/Contact";

export function App() {
  return (
    <ExperienceProvider>
      <AudioProvider>
        <a className="skip-link" href="#main">
          Skip to content
        </a>
        <Header />
        <main id="main">
          <Hero />
          <Proof />
          <Statement />
          <Narrative />

          {/* 3D Taxonomic Galaxy */}
          <section className="section constellation-section" id="constellation" aria-label="3D Taxonomic Galaxy">
            <div className="section-header">
              <p className="eyebrow">Spatial Bioacoustic Network</p>
              <h2>Real-time 3D<br />taxonomic <em>topology.</em></h2>
              <p className="section-deck">
                Explore acoustic detections distributed across frequency space and taxonomic relationships in an
                interactive 3D orbital cluster.
              </p>
            </div>
            <SpeciesConstellation3D />
          </section>

          {/* Real-time Bioacoustic Soundboard */}
          <InteractiveSoundboard />

          {/* Verifiable Provenance Evidence Demo */}
          <EvidenceDemo />

          {/* Transparent pilot planning scenario */}
          <RoiCalculator />

          {/* Enterprise Governance, Data Sovereignty & Field Protocol */}
          <EnterpriseGovernance />

          <Pilot />
          <Partners />
          <Budget />
          <Boundary />
          <Closing />
          <Contact />
        </main>
        <Footer />
      </AudioProvider>
    </ExperienceProvider>
  );
}
