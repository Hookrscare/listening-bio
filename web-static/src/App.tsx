import { ExperienceProvider } from "./providers/ExperienceProvider";
import { AudioProvider } from "./providers/AudioProvider";
import { Header } from "./components/layout/Header";
import { Footer } from "./components/layout/Footer";
import { Hero } from "./components/hero/Hero";
import { Narrative } from "./components/narrative/Narrative";
import { EvidenceDemo } from "./components/evidence/EvidenceDemo";
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
          <EvidenceDemo />
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
