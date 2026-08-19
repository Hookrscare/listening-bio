import { useState } from "react";

type ReadinessTab = "controls" | "pilot" | "commercial";

const TABS: Array<{ id: ReadinessTab; label: string }> = [
  { id: "controls", label: "01 / Evidence controls" },
  { id: "pilot", label: "02 / Pilot protocol" },
  { id: "commercial", label: "03 / Commercial readiness" },
];

export function EnterpriseGovernance() {
  const [activeTab, setActiveTab] = useState<ReadinessTab>("controls");

  return (
    <section
      className="section enterprise-governance-section"
      id="governance"
      aria-labelledby="governance-heading"
    >
      <div className="section-header">
        <p className="eyebrow">Readiness you can inspect</p>
        <h2 id="governance-heading">
          Separate what works now<br />
          from <em>what comes next.</em>
        </h2>
        <p className="section-deck">
          The platform preserves source context, model provenance, and review
          history today. Field validation, contracting, and assurance remain
          explicit milestones for the founding pilot.
        </p>
      </div>

      <div className="governance-tabs" role="tablist" aria-label="Readiness areas">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            id={`readiness-tab-${tab.id}`}
            type="button"
            role="tab"
            aria-controls={`readiness-panel-${tab.id}`}
            aria-selected={activeTab === tab.id}
            className={`tab-btn ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="governance-content-card">
        {activeTab === "controls" && (
          <div
            className="tab-pane"
            id="readiness-panel-controls"
            role="tabpanel"
            aria-labelledby="readiness-tab-controls"
          >
            <div className="pane-grid">
              <div className="pane-block">
                <span className="mini-eyebrow">IMPLEMENTED CONTROLS</span>
                <h3>Evidence stays connected to its source</h3>
                <p>
                  Uploaded WAV files receive SHA-256 checksums. Candidate
                  detections retain their model context, time windows, and
                  confidence, while review events preserve the decision trail.
                </p>
                <ul className="check-list">
                  <li>Source audio checksum and file metadata.</li>
                  <li>Model registry, inference context, and normalized detections.</li>
                  <li>Append-only confirmed, uncertain, and rejected review events.</li>
                </ul>
              </div>

              <div className="pane-block">
                <span className="mini-eyebrow">CURRENT BOUNDARY</span>
                <h3>Governance terms remain drafts</h3>
                <p>
                  Client ownership, retention schedules, sensitive-location
                  handling, and private-data training restrictions are proposed
                  contract terms. They require partner agreement and legal review.
                </p>
                <div className="governance-badge-box">
                  <span className="badge-item">Live: evidence provenance</span>
                  <span className="badge-item">Draft: TNFD evidence support</span>
                  <span className="badge-item">Draft: ESRS E4 evidence support</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "pilot" && (
          <div
            className="tab-pane"
            id="readiness-panel-pilot"
            role="tabpanel"
            aria-labelledby="readiness-tab-pilot"
          >
            <div className="pane-grid">
              <div className="pane-block">
                <span className="mini-eyebrow">FOUNDING PILOT DRAFT</span>
                <h3>A bounded, reproducible field study</h3>
                <p>
                  The proposed protocol covers three to five partner-approved
                  sites over 30 days. Sampling schedules, equipment settings,
                  reviewer criteria, and reporting thresholds will be finalized
                  with the scientific and site partners before deployment.
                </p>
                <div className="protocol-steps">
                  <div className="step-item">
                    <strong>Phase 1: Approve the protocol</strong>
                    <span>Site access, monitoring question, equipment, and safeguards.</span>
                  </div>
                  <div className="step-item">
                    <strong>Phase 2: Collect and process</strong>
                    <span>Target 50–100 WAV files with documented BirdNET settings.</span>
                  </div>
                  <div className="step-item">
                    <strong>Phase 3: Review and report</strong>
                    <span>Qualified reviewer decisions, exports, limitations, and next steps.</span>
                  </div>
                </div>
              </div>

              <div className="pane-block">
                <span className="mini-eyebrow">REQUIRED PARTNER</span>
                <h3>Scientific review is a gate, not a claim</h3>
                <p>
                  Automated detections remain candidates until a named,
                  qualified reviewer approves the protocol and validates the
                  agreed sample. Listening.bio is actively seeking that partner.
                </p>
                <a
                  className="secondary"
                  href="mailto:rodrigo@listening.bio?subject=Listening.bio%20pilot%20protocol%20draft"
                >
                  Request the protocol draft <span aria-hidden="true">↗</span>
                </a>
              </div>
            </div>
          </div>
        )}

        {activeTab === "commercial" && (
          <div
            className="tab-pane"
            id="readiness-panel-commercial"
            role="tabpanel"
            aria-labelledby="readiness-tab-commercial"
          >
            <div className="pane-grid">
              <div className="pane-block">
                <span className="mini-eyebrow">PURCHASABLE FIRST STEP</span>
                <h3>A focused $10,000 founding pilot</h3>
                <p>
                  The proposed package is deliberately narrow: one monitoring
                  question, three to five sites, a reviewed dataset, map, CSV
                  exports, and a conservative evidence memo.
                </p>
                <ul className="check-list">
                  <li>Scope, acceptance criteria, and payment milestones in writing.</li>
                  <li>Travel, equipment, and expert-review allowances defined before signing.</li>
                  <li>No certification, regulatory assurance, or comprehensive inventory claim.</li>
                </ul>
              </div>

              <div className="pane-block">
                <span className="mini-eyebrow">BEFORE FIELDWORK</span>
                <h3>Contracting controls still to complete</h3>
                <p>
                  The SOW, data terms, reviewer agreement, insurance, and service
                  costs are working drafts. Final terms will be reviewed and
                  bound before a paid deployment begins.
                </p>
                <div className="margin-card">
                  <div className="margin-row">
                    <span>Platform workflow</span>
                    <strong className="low-cost">Operational</strong>
                  </div>
                  <div className="margin-row">
                    <span>Field evidence</span>
                    <strong className="high-cost">Partner required</strong>
                  </div>
                  <div className="margin-row">
                    <span>Commercial terms</span>
                    <strong>Draft</strong>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
