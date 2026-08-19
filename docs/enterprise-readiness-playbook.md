# Enterprise Readiness Working Draft

This document tracks the commercial, legal, scientific, and operational work required before Listening.bio signs an enterprise or institutional field-monitoring engagement. It is an internal planning document, not evidence that the requirements below have been completed.

## Status Summary

| Requirement | Current status | Exit criterion |
| --- | --- | --- |
| Qualified ecological reviewer | Not secured | Named reviewer, verified credentials, signed agreement |
| Local field pilot | Not completed | Partner-approved protocol and reviewed local dataset |
| Publishable case study | Simulation only | Written partner permission and verified results |
| Evidence exports | Prototype implemented | Partner QA and versioned sample package |
| Data ownership and retention terms | Draft | Counsel-reviewed terms accepted by client |
| Business insurance | Not verified | Certificates of insurance for required policies |
| Proposal, SOW, and agreement | Draft structure | Counsel-reviewed templates ready for signature |
| Service costs and margin | Assumptions only | Measured pilot costs and approved pricing model |
| Field protocol | Draft | Scientific and site-partner approval |

## 1. Qualified Ecological Reviewer

### Purpose

Automated detections are evidence candidates. A qualified ecologist, ornithologist, or bioacoustics researcher must approve the review protocol and validate the agreed sample before a pilot report presents confirmed observations.

### Draft reviewer workflow

1. Define the sampling and escalation rules before analysis.
2. Review source audio, spectrogram, timing, model label, and confidence.
3. Record `Confirmed`, `Uncertain`, or `Rejected` as an append-only review event.
4. Preserve reviewer identity, timestamp, notes, and original model output.

The application supports reviewer-linked events. It does not currently provide cryptographic reviewer signatures or an external assurance opinion.

### Completion evidence

- Verified reviewer qualifications
- Signed contractor or collaboration agreement
- Agreed rate, conflicts policy, turnaround target, and attribution terms

## 2. Founding Field Pilot

### Proposed scope

| Parameter | Planning target |
| --- | --- |
| Duration | 30 days |
| Sites | 3 to 5 partner-approved locations |
| Recordings | 50 to 100 usable WAV files |
| Analysis | Documented BirdNET configuration and normalized candidates |
| Review | Qualified review of the agreed representative sample |
| Deliverables | Dataset, map, CSV exports, evidence memo, and limitations |

Sampling windows, equipment, gain, mounting, weather controls, and sensitive-location handling must be approved by the scientific and site partners. These values are planning targets, not completed field results.

## 3. Case Study and Publication Permission

The Central Park material in `docs/central-park-pilot-simulation.md` is a planning simulation. It must never be presented as a completed deployment or as evidence of species presence, recording hours, savings, or monitoring performance.

A publishable case study requires:

- Partner identity and site permission
- Verified methods and dates
- Source-linked, reviewed results
- Explicit permission for every public metric and quotation
- Sensitive-location review before publication

Draft permission language must be reviewed by the partner and legal counsel before use.

## 4. Prototype Evidence Exports

Implemented API exports include:

- `GET /exports/detections.csv?project_id={project_id}`
- `GET /exports/sites.geojson?project_id={project_id}`
- `GET /exports/detections.geojson?project_id={project_id}`
- `GET /exports/evidence-package.md?project_id={project_id}`
- `GET /exports/tnfd-evidence-draft.json?project_id={project_id}`
- `GET /exports/esrs-e4-evidence-draft.json?project_id={project_id}`

The framework exports organize supporting evidence only. They are not TNFD or ESRS disclosures, certifications, assurance opinions, or compliance determinations.

## 5. Data Ownership, Privacy, and Retention

### Proposed client terms

- The client retains ownership of its raw audio and supplied metadata.
- Private client audio is not used to train commercial models without written permission.
- Retention, deletion, backup, and export periods are defined in the engagement agreement.
- Sensitive species coordinates are restricted or generalized according to the approved protocol.

These are proposed terms. The current local-storage implementation does not yet provide client-configurable lifecycle policies, object lock, direct S3/R2 upload, or automated sensitive-coordinate classification.

## 6. Insurance

Required coverage depends on the client, field activity, jurisdiction, and contract. Likely categories include commercial general liability, technology errors and omissions, cyber liability, workers' compensation, and equipment coverage.

No public statement should claim that coverage is active until current certificates have been verified. Obtain broker quotes after the pilot scope and field responsibilities are known.

## 7. Proposal, SOW, and Agreement

The initial written package should define:

- Monitoring question, sites, exclusions, and partner responsibilities
- Equipment, field access, data transfer, and review method
- Deliverables, acceptance criteria, schedule, and payment milestones
- Data rights, confidentiality, retention, publication permission, and deletion
- Scientific limitations and prohibited claims
- Liability, insurance, cancellation, and dispute terms

The current material is a structure for counsel review, not a turnkey MSA or binding service-level agreement.

## 8. Unit Economics

Do not publish an 80% margin, a 70% savings claim, or a cost comparison until the assumptions have been measured in a real pilot.

Track the following separately:

- Equipment purchase, loss, replacement, and useful life
- Travel, permits, deployment, retrieval, and local coordination
- Storage, processing, data transfer, and backup
- Scientific protocol design and review time
- Engineering support, reporting, revisions, and insurance

The website may present a transparent planning scenario. Final pricing and margin targets must be based on observed delivery costs.

## 9. Draft Field Protocol

The protocol must record device model, firmware, enclosure, microphone orientation, mounting method, sample rate, bit depth, gain, duty cycle, time zone, weather, habitat notes, calibration method, and chain of custody.

Recommended values should not be hard-coded across every habitat and device. A qualified scientific reviewer should approve equipment-specific settings and calibration before deployment.

## Release Gate

Before calling the service enterprise-ready, confirm all of the following:

- [ ] Named scientific reviewer and signed agreement
- [ ] Partner and site permission
- [ ] Approved protocol and safety plan
- [ ] Insurance certificates required by the engagement
- [ ] Counsel-reviewed SOW and data terms
- [ ] Completed field pilot with source-linked review
- [ ] Measured costs and approved pricing
- [ ] Publishable case study permission
- [ ] Evidence package independently checked against source records
