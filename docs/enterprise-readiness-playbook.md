# Enterprise Readiness Playbook: The 9 Corporate Requirements for listening.bio

This document provides the complete commercial, legal, scientific, and operational assets required before pitching and signing enterprise / corporate clients (Renewable Energy, Mining, Infrastructure, Forestry, ESG Funds).

---

## Table of Contents
1. [Qualified Ecological Reviewer Protocol & Agreement](#1-qualified-ecological-reviewer-protocol--agreement)
2. [30-Day Local Field Pilot Execution Plan](#2-30-day-local-field-pilot-execution-plan)
3. [Real Case Study Structure & Publication Release](#3-real-case-study-structure--publication-release)
4. [Sample Evidence & TNFD Audit Report](#4-sample-evidence--tnfd-audit-report)
5. [Data Ownership, Privacy & Retention Terms (DPA / MSA Clause)](#5-data-ownership-privacy--retention-terms)
6. [Professional Liability & Business Insurance Specifications](#6-professional-liability--business-insurance)
7. [Standard Proposal, Scope of Work (SOW) & Master Services Agreement (MSA)](#7-standard-proposal-sow--msa)
8. [Unit Economics, Documented Service Costs & Margin Model](#8-unit-economics-service-costs--target-margin)
9. [Standard Operating Procedure: Reproducible Field PAM Audio Protocol](#9-sop-reproducible-field-pam-audio-protocol)

---

## 1. Qualified Ecological Reviewer Protocol & Agreement

### Role Definition
Corporate ESG auditors (TNFD / CSRD) reject purely automated AI detections. Every compliance package must include secondary review by a **Qualified Ecological Reviewer** (credentialed ornithologist, bioacoustician, or wildlife biologist with M.Sc. / Ph.D. or 5+ years field survey experience).

### Reviewer Workflow
1. **Sample Batch Selection**: System automatically flags high-uncertainty detections (confidence 0.35–0.70) and all candidate red-listed species.
2. **Spectrogram & Audio Scrub**: Reviewer listens to a 3-second focus window and inspects the frequency contour.
3. **Status Stamping**: Reviewer signs off: `Confirmed`, `Uncertain`, or `Rejected`.
4. **Cryptographic Signing**: Reviewer ID, timestamp, and notes are immutably attached to the detection record.

### Retainer / Contractor Agreement Terms
* **Rate**: $85–$120 / hour or $0.75 per verified detection candidate window.
* **Turnaround SLA**: 48 hours for monthly batch review.
* **Independence**: Reviewer certifies no financial conflict of interest with the corporate client.

---

## 2. 30-Day Local Field Pilot Execution Plan

### Objective
Deploy 3–5 sensor hubs across representative local sites (e.g. urban woodland, riparian corridor, open meadow) for 30 consecutive days to generate real baseline acoustic datasets.

| Parameter | Specification |
| :--- | :--- |
| **Duration** | 30 Continuous Days (720 hours per sensor station) |
| **Stations** | 3 to 5 passive acoustic monitors (AudioMoth / Song Meter Micro) |
| **Schedule** | Duty cycle: 1 minute on / 4 minutes off (or 2 hrs dawn + 2 hrs dusk continuous) |
| **Target Data Yield** | 100 to 250 high-quality WAV files (24-bit/48kHz mono) |
| **Target Deliverable** | Baseline Acoustic Index (NDSI), Species Richness Curve, Verified Detection Matrix |

---

## 3. Real Case Study Structure & Publication Release

### Case Study Framework: "Continuous Acoustic Monitoring at Central Park Urban Corridor"
* **Executive Summary**: How continuous PAM revealed 14 additional bird species undetected during episodic manual daytime surveys.
* **Methodology**: 5 sensor nodes recording across dawn chorus and dusk flights; BirdNET Analyzer inference with expert human review.
* **Findings**:
  * Total recording hours: 120.5 hours.
  * Candidate detections: 342.
  * Verified species richness: 18 distinct avian species (American Robin, Northern Cardinal, Wood Thrush, Great Horned Owl, etc.).
  * Cost comparison: 68% lower cost per observation hour compared to traditional consultant point counts.

### Client Release & Consent Clause
> *"Client grants listening.bio permission to reference the Project name, anonymized acoustic trends, and aggregate species richness metrics in public case studies, marketing materials, and regulatory methodology whitepapers, provided exact geolocations of sensitive taxa are obscured."*

---

## 4. Sample Evidence & TNFD Audit Report

The platform exports complete, audit-ready compliance packages:
* **JSON Format**: `/exports/tnfd-biodiversity.json` (Structured for ingestion into enterprise ESG data systems).
* **CSV Format**: `/exports/detections.csv` (Includes raw WAV SHA-256 hashes, timestamps, confidence scores, and reviewer decisions).
* **Markdown Package**: `/exports/evidence-package.md` (Executive summary with audit disclaimers, methodology boundaries, and species frequency matrices).

---

## 5. Data Ownership, Privacy & Retention Terms

### Enterprise Data Sovereignty (MSA Clause)
1. **Client Ownership**: The Client retains 100% exclusive ownership of all raw audio files, metadata, GPS coordinates, and generated biodiversity reports.
2. **No Unapproved AI Training**: listening.bio agrees never to use Client's private audio recordings to train commercial models without express written authorization.
3. **Retention & Archival**: Raw WAV files are retained in client-designated cloud storage (AWS S3 / GCP Cloud Storage / Azure Blob) with lifecycle rules (e.g., Hot storage for 90 days, Glacier/Coldline for 5 years).
4. **Sensitive Species Protection**: GPS coordinates of IUCN red-listed or state-threatened species are blurred to a 10km grid resolution in public-facing dashboards to prevent poaching or disturbance.

---

## 6. Professional Liability & Business Insurance

Before executing corporate contracts over $25,000, maintain the following coverage:

| Policy Type | Recommended Limit | Purpose |
| :--- | :--- | :--- |
| **Commercial General Liability (CGL)** | $1,000,000 / $2,000,000 | Bodily injury & property damage during field sensor deployment |
| **Technology Errors & Omissions (E&O)** | $1,000,000 / $2,000,000 | Software defects, algorithmic misclassification, SLA breaches |
| **Cyber Liability & Data Breach** | $1,000,000 | Cloud data loss, unauthorized access, client data exfiltration |
| **Workers' Compensation** | Statutory | Required for field technicians deploying sensor hardware |

---

## 7. Standard Proposal, Scope of Work (SOW) & Master Services Agreement (MSA)

### SOW Structure
* **Section 1: Scope of Monitoring**: Station count, geographic boundary, target taxonomic groups.
* **Section 2: Deliverables Schedule**:
  * *Day 1–5*: Sensor deployment, acoustic baseline calibration.
  * *Day 15*: Mid-pilot health check & telemetry verification.
  * *Day 35*: Final Verified Biodiversity Evidence Package + TNFD Audit Report.
* **Section 3: Fee Schedule**: 50% on contract execution, 50% on final report delivery.
* **Section 4: Limitation of Liability**: Liability capped at the total contract value paid over the preceding 12 months.

---

## 8. Unit Economics, Service Costs & Target Margin

```
[ Traditional Survey Model ]           [ listening.bio SaaS Model ]
  Field Biologist: $12,000/mo            Hardware Hub: $399 (Amortized over 3 yrs = $11/mo)
  Travel & Lodging: $2,500/mo            Cellular IoT Data: $12/mo
  Report Prep: $3,000/mo                 Cloud GPU/Inference: $15/mo
  TOTAL: $17,500 / month                 TOTAL COGS: $38 / month per station
                                         REVENUE BILLED: $249 / month per station
                                         GROSS MARGIN: 84.7%
```

### Margin Structure
* **Gross Margin on SaaS Subscriptions**: **82% – 88%**.
* **Gross Margin on Sensor Hardware (HaaS)**: **45% – 55%**.
* **Gross Margin on Expert Ecological Review Retainer**: **40% – 50%**.
* **Blended Corporate Account Margin**: **74.5%**.

---

## 9. SOP: Reproducible Field PAM Audio Protocol

### Hardware Setup
1. **Device**: AudioMoth v1.2 / Song Meter Micro inside IP67 weatherproof acoustic enclosure.
2. **Mounting**: Fixed to tree trunk or post at **1.5m to 2.0m height**, facing away from prevailing high-wind direction.
3. **Gain**: Medium / High (+30.6 dB).
4. **Sample Rate**: 48.0 kHz, 16-bit uncompressed WAV (captures acoustic range from 100 Hz up to 24 kHz Nyquist limit).
5. **Duty Cycle**:
   * *Dawn Window* (05:00 – 08:30): 1 min record / 2 min sleep.
   * *Dusk Window* (18:00 – 21:00): 1 min record / 2 min sleep.
   * *Nocturnal / Day Sampling*: 1 min record every 10 min.
6. **Calibration**: Perform acoustic test tone check (1 kHz sine sweep) at deployment to verify microphone membrane integrity.
