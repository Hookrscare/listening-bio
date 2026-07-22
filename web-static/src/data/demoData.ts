// Representative demonstration data for the interactive evidence workspace.
// EVERYTHING here is clearly labeled demonstrationOnly. These are not scientific
// findings and imply no site-level biodiversity conclusion (spec §6, §20).
//
// The provenance is anchored to a REAL, properly licensed public recording:
// Xeno-canto XC364638 (American Robin, Turdus migratorius), recordist Ted Floyd,
// CC BY-NC-SA 4.0. The detection windows below are representative examples for
// interface demonstration, consistent with the repo's verified BirdNET run that
// produced 7 candidates including 4 American Robin windows.

export type ReviewStatus =
  | "unreviewed"
  | "confirmed"
  | "rejected"
  | "uncertain";

export interface DemoDetection {
  id: string;
  label: string;
  scientificName?: string;
  detectionType: "species" | "sound_class";
  confidence: number;
  startSeconds: number;
  endSeconds: number;
  frequencyMinHz: number;
  frequencyMaxHz: number;
  defaultReview: ReviewStatus;
  demonstrationOnly: true;
}

export interface DemoProvenance {
  recordingId: string;
  recordingTitle: string;
  recordedAt: string;
  locationLabel: string;
  latitude: number;
  longitude: number;
  habitat: string;
  recorder: string;
  sampleRateHz: number;
  channelCount: number;
  sourceLicense: string;
  sourceLicenseUrl: string;
  sourceUrl: string;
  fileChecksum: string;
  modelName: string;
  modelVersion: string;
  modelLocale: string;
  confidenceThreshold: number;
  processingTime: string;
  evidenceLevel: "simulation" | "public_data" | "field";
  demonstrationOnly: true;
}

export const DEMO_AUDIO_SRC = "./demo/xc364638-american-robin.mp3";
export const DEMO_SPECTROGRAM_SRC = "./demo/xc364638-spectrogram.svg";

export const DEMO_PROVENANCE: DemoProvenance = {
  recordingId: "XC364638",
  recordingTitle: "American Robin — Xeno-canto XC364638",
  recordedAt: "2017-03-28",
  locationLabel: "Lafayette, Boulder County, Colorado, United States",
  latitude: 39.9936,
  longitude: -105.0897,
  habitat: "Suburban edge / open woodland",
  recorder: "Ted Floyd",
  sampleRateHz: 48000,
  channelCount: 1,
  sourceLicense: "CC BY-NC-SA 4.0",
  sourceLicenseUrl: "https://creativecommons.org/licenses/by-nc-sa/4.0/",
  sourceUrl: "https://xeno-canto.org/364638",
  fileChecksum: "sha256:demo-representative-checksum",
  modelName: "BirdNET",
  modelVersion: "Analyzer (representative demo run)",
  modelLocale: "en_us",
  confidenceThreshold: 0.25,
  processingTime: "representative",
  evidenceLevel: "public_data",
  demonstrationOnly: true,
};

// Representative candidate windows. Includes confirmed / rejected / uncertain /
// unreviewed so every review state is shown, and rejected/uncertain remain
// first-class and visible in the UI and exports (spec §6).
export const DEMO_DETECTIONS: DemoDetection[] = [
  {
    id: "det-1",
    label: "American Robin",
    scientificName: "Turdus migratorius",
    detectionType: "species",
    confidence: 0.91,
    startSeconds: 1.5,
    endSeconds: 4.5,
    frequencyMinHz: 1800,
    frequencyMaxHz: 3600,
    defaultReview: "confirmed",
    demonstrationOnly: true,
  },
  {
    id: "det-2",
    label: "American Robin",
    scientificName: "Turdus migratorius",
    detectionType: "species",
    confidence: 0.74,
    startSeconds: 6.0,
    endSeconds: 9.0,
    frequencyMinHz: 1900,
    frequencyMaxHz: 3400,
    defaultReview: "confirmed",
    demonstrationOnly: true,
  },
  {
    id: "det-3",
    label: "American Robin",
    scientificName: "Turdus migratorius",
    detectionType: "species",
    confidence: 0.52,
    startSeconds: 11.0,
    endSeconds: 14.0,
    frequencyMinHz: 1700,
    frequencyMaxHz: 3500,
    defaultReview: "uncertain",
    demonstrationOnly: true,
  },
  {
    id: "det-4",
    label: "American Robin",
    scientificName: "Turdus migratorius",
    detectionType: "species",
    confidence: 0.38,
    startSeconds: 16.5,
    endSeconds: 19.5,
    frequencyMinHz: 2000,
    frequencyMaxHz: 3300,
    defaultReview: "unreviewed",
    demonstrationOnly: true,
  },
  {
    id: "det-5",
    label: "House Finch",
    scientificName: "Haemorhous mexicanus",
    detectionType: "species",
    confidence: 0.29,
    startSeconds: 21.0,
    endSeconds: 24.0,
    frequencyMinHz: 2400,
    frequencyMaxHz: 4200,
    defaultReview: "rejected",
    demonstrationOnly: true,
  },
];

export interface DemoSite {
  siteId: string;
  name: string;
  habitatType: string;
  latitude: number;
  longitude: number;
  evidenceLevel: "simulation";
  claimStatus: string;
}

// Representative site network (from the repo's clearly-labeled Central Park
// pilot SIMULATION dataset). Simulation only — not field evidence.
export const DEMO_SITES: DemoSite[] = [
  {
    siteId: "1b36a4ef",
    name: "Hallett Nature Sanctuary",
    habitatType: "restored woodland / pond edge",
    latitude: 40.7665,
    longitude: -73.9733,
    evidenceLevel: "simulation",
    claimStatus: "Demo rehearsal only",
  },
  {
    siteId: "08949ef7",
    name: "Jacqueline Kennedy Onassis Reservoir",
    habitatType: "open water edge",
    latitude: 40.7851,
    longitude: -73.959,
    evidenceLevel: "simulation",
    claimStatus: "Demo rehearsal only",
  },
  {
    siteId: "ec5a676c",
    name: "North Woods",
    habitatType: "mature woodland / ravine",
    latitude: 40.7975,
    longitude: -73.9567,
    evidenceLevel: "simulation",
    claimStatus: "Demo rehearsal only",
  },
  {
    siteId: "0589f222",
    name: "Sheep Meadow",
    habitatType: "open lawn / urban edge",
    latitude: 40.7711,
    longitude: -73.9741,
    evidenceLevel: "simulation",
    claimStatus: "Demo rehearsal only",
  },
  {
    siteId: "823ea63c",
    name: "The Ramble",
    habitatType: "woodland understory / migratory stopover",
    latitude: 40.7772,
    longitude: -73.9694,
    evidenceLevel: "simulation",
    claimStatus: "Demo rehearsal only",
  },
];
