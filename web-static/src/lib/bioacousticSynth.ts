// Web Audio synthesis for an explicitly non-scientific interface demonstration.
// Patterns are species-inspired and must not be presented as recordings or model evidence.

export interface SpeciesPreset {
  id: string;
  name: string;
  scientificName: string;
  family: string;
  frequencyRange: string;
  confidence: number;
  description: string;
  tags: string[];
}

export const SPECIES_PRESETS: SpeciesPreset[] = [
  {
    id: "robin",
    name: "American Robin",
    scientificName: "Turdus migratorius",
    family: "Turdidae",
    frequencyRange: "1.8 kHz – 3.6 kHz",
    confidence: 0.94,
    description: "Clear, cheerful caroling whistling phrases in repeated rhythmic triplets.",
    tags: ["Dawn Chorus", "Woodland", "High Confidence"],
  },
  {
    id: "cardinal",
    name: "Northern Cardinal",
    scientificName: "Cardinalis cardinalis",
    family: "Cardinalidae",
    frequencyRange: "2.0 kHz – 4.2 kHz",
    confidence: 0.88,
    description: "Loud, liquid, rapid slurred whistles descending into metallic chirps.",
    tags: ["Edge Habitat", "Clear Signal", "Year-round"],
  },
  {
    id: "thrush",
    name: "Wood Thrush",
    scientificName: "Hylocichla mustelina",
    family: "Turdidae",
    frequencyRange: "2.2 kHz – 5.5 kHz",
    confidence: 0.91,
    description: "Ethereal, flute-like bell harmonics produced simultaneously by bifurcated syrinx.",
    tags: ["Forest Canopy", "Sensitive Indicator", "Summer Resident"],
  },
  {
    id: "owl",
    name: "Great Horned Owl",
    scientificName: "Bubo virginianus",
    family: "Strigidae",
    frequencyRange: "250 Hz – 600 Hz",
    confidence: 0.85,
    description: "Resonant, low-frequency rhythmic territorial hoots with deep acoustic penetration.",
    tags: ["Nocturnal", "Apex Predator", "Low Frequency"],
  },
  {
    id: "chorus",
    name: "Dawn Chorus Mix",
    scientificName: "Bioacoustic Soundscape",
    family: "Multi-Taxa",
    frequencyRange: "200 Hz – 8.0 kHz",
    confidence: 0.96,
    description: "Composite acoustic biodiversity index representing multi-species biophony at sunrise.",
    tags: ["Ecosystem Index", "NDSI > 0.82", "Peak Activity"],
  },
];

let globalAudioCtx: AudioContext | null = null;

function getAudioContext(): AudioContext {
  if (!globalAudioCtx || globalAudioCtx.state === "closed") {
    const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    globalAudioCtx = new AudioCtx();
  }
  if (globalAudioCtx.state === "suspended") {
    globalAudioCtx.resume().catch(() => {});
  }
  return globalAudioCtx;
}

export function playBioacousticSound(
  speciesId: string,
  onFrequencyUpdate?: (fft: Float32Array) => void,
): () => void {
  const ctx = getAudioContext();
  const now = ctx.currentTime;
  let isCancelled = false;

  const masterGain = ctx.createGain();
  masterGain.gain.setValueAtTime(0.18, now);

  const analyser = ctx.createAnalyser();
  analyser.fftSize = 128;
  masterGain.connect(analyser);
  analyser.connect(ctx.destination);

  let intervalId: number | null = null;
  if (onFrequencyUpdate) {
    const dataArray = new Float32Array(analyser.frequencyBinCount);
    intervalId = window.setInterval(() => {
      if (isCancelled) return;
      analyser.getFloatFrequencyData(dataArray);
      onFrequencyUpdate(dataArray);
    }, 40);
  }

  const stopAudio = () => {
    isCancelled = true;
    if (intervalId !== null) clearInterval(intervalId);
    try {
      masterGain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.1);
      setTimeout(() => {
        masterGain.disconnect();
      }, 150);
    } catch {
      // Ignored
    }
  };

  switch (speciesId) {
    case "robin": {
      // Robin phrases: 3 melodious chirps with vibrato
      const notes = [2200, 2600, 2400, 2800, 2300];
      notes.forEach((baseFreq, i) => {
        const t = now + i * 0.38;
        const osc = ctx.createOscillator();
        const g = ctx.createGain();

        osc.type = "sine";
        osc.frequency.setValueAtTime(baseFreq, t);
        osc.frequency.exponentialRampToValueAtTime(baseFreq * 1.25, t + 0.12);
        osc.frequency.exponentialRampToValueAtTime(baseFreq * 0.95, t + 0.28);

        g.gain.setValueAtTime(0.001, t);
        g.gain.linearRampToValueAtTime(0.25, t + 0.04);
        g.gain.exponentialRampToValueAtTime(0.001, t + 0.32);

        osc.connect(g);
        g.connect(masterGain);
        osc.start(t);
        osc.stop(t + 0.35);
      });
      setTimeout(stopAudio, 2200);
      break;
    }

    case "cardinal": {
      // Cardinal rapid down-sweeps: "cheer cheer cheer wheet wheet"
      for (let i = 0; i < 4; i++) {
        const t = now + i * 0.32;
        const osc = ctx.createOscillator();
        const g = ctx.createGain();

        osc.type = "sine";
        osc.frequency.setValueAtTime(3600, t);
        osc.frequency.exponentialRampToValueAtTime(2100, t + 0.24);

        g.gain.setValueAtTime(0.001, t);
        g.gain.linearRampToValueAtTime(0.3, t + 0.03);
        g.gain.exponentialRampToValueAtTime(0.001, t + 0.26);

        osc.connect(g);
        g.connect(masterGain);
        osc.start(t);
        osc.stop(t + 0.28);
      }
      setTimeout(stopAudio, 1800);
      break;
    }

    case "thrush": {
      // Wood Thrush harmonic dual syrinx: overlapping bell-tones
      const chords = [
        [2400, 3600],
        [2800, 4200],
        [3200, 4800],
      ];
      chords.forEach((chord, i) => {
        const t = now + i * 0.45;
        chord.forEach((freq) => {
          const osc = ctx.createOscillator();
          const g = ctx.createGain();

          osc.type = "sine";
          osc.frequency.setValueAtTime(freq, t);
          osc.frequency.linearRampToValueAtTime(freq * 1.08, t + 0.2);
          osc.frequency.linearRampToValueAtTime(freq * 0.98, t + 0.38);

          g.gain.setValueAtTime(0.001, t);
          g.gain.linearRampToValueAtTime(0.18, t + 0.05);
          g.gain.exponentialRampToValueAtTime(0.001, t + 0.42);

          osc.connect(g);
          g.connect(masterGain);
          osc.start(t);
          osc.stop(t + 0.44);
        });
      });
      setTimeout(stopAudio, 2000);
      break;
    }

    case "owl": {
      // Great Horned Owl: low resonant territorial hoots
      const hoots = [0, 0.4, 0.9, 1.3, 1.8];
      hoots.forEach((offset, idx) => {
        const t = now + offset;
        const osc = ctx.createOscillator();
        const g = ctx.createGain();

        osc.type = "sine";
        const freq = idx === 0 || idx === 3 ? 320 : 280;
        osc.frequency.setValueAtTime(freq, t);
        osc.frequency.linearRampToValueAtTime(freq * 1.05, t + 0.1);
        osc.frequency.linearRampToValueAtTime(freq * 0.95, t + 0.25);

        g.gain.setValueAtTime(0.001, t);
        g.gain.linearRampToValueAtTime(0.35, t + 0.06);
        g.gain.exponentialRampToValueAtTime(0.001, t + 0.32);

        osc.connect(g);
        g.connect(masterGain);
        osc.start(t);
        osc.stop(t + 0.35);
      });
      setTimeout(stopAudio, 2500);
      break;
    }

    case "chorus":
    default: {
      // Dawn Chorus layered ambient soundscape
      for (let i = 0; i < 8; i++) {
        const t = now + i * 0.25;
        const osc = ctx.createOscillator();
        const g = ctx.createGain();
        const freq = 1800 + ((i * 370) % 2400);

        osc.type = i % 2 === 0 ? "sine" : "triangle";
        osc.frequency.setValueAtTime(freq, t);
        osc.frequency.exponentialRampToValueAtTime(freq * (1 + (i % 3) * 0.15), t + 0.18);

        g.gain.setValueAtTime(0.001, t);
        g.gain.linearRampToValueAtTime(0.14, t + 0.04);
        g.gain.exponentialRampToValueAtTime(0.001, t + 0.28);

        osc.connect(g);
        g.connect(masterGain);
        osc.start(t);
        osc.stop(t + 0.3);
      }
      setTimeout(stopAudio, 2800);
      break;
    }
  }

  return stopAudio;
}
