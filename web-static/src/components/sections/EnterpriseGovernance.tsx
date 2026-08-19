import { useState } from "react";

export function EnterpriseGovernance() {
  const [activeTab, setActiveTab] = useState<"governance" | "pilot" | "protocol">("governance");

  return (
    <section className="section enterprise-governance-section" id="governance" aria-labelledby="governance-heading">
      <div className="section-header">
        <p className="eyebrow">Enterprise Governance & Standards</p>
        <h2 id="governance-heading">
          Institutional rigor.<br />
          <em>Built for compliance.</em>
        </h2>
        <p className="section-deck">
          Listening.bio operates under strict scientific protocols, client-exclusive data ownership, and transparent
          methodologies required by institutional ESG audits and environmental impact authorities.
        </p>
      </div>

      <div className="governance-tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "governance"}
          className={`tab-btn ${activeTab === "governance" ? "active" : ""}`}
          onClick={() => setActiveTab("governance")}
        >
          01 / Data Ownership & Privacy
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "pilot"}
          className={`tab-btn ${activeTab === "pilot" ? "active" : ""}`}
          onClick={() => setActiveTab("pilot")}
        >
          02 / 30-Day Field Pilot Protocol
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "protocol"}
          className={`tab-btn ${activeTab === "protocol" ? "active" : ""}`}
          onClick={() => setActiveTab("protocol")}
        >
          03 / Standard SOW & Assurance
        </button>
      </div>

      <div className="governance-content-card">
        {activeTab === "governance" && (
          <div className="tab-pane">
            <div className="pane-grid">
              <div className="pane-block">
                <span className="mini-eyebrow">CLIENT DATA SOVEREIGNTY</span>
                <h3>100% Client-Owned Raw Audio</h3>
                <p>
                  All audio recordings, acoustic hashes, and geographic coordinates remain the exclusive intellectual
                  property of the client. Listening.bio never trains third-party commercial models on private field data
                  without explicit written consent.
                </p>
                <ul className="check-list">
                  <li>Client-controlled data retention (30 days to 10+ years archival).</li>
                  <li>Cryptographic SHA-256 integrity hashes on every uploaded WAV file.</li>
                  <li>Zero unverified public sharing of sensitive/threatened species coordinates.</li>
                </ul>
              </div>

              <div className="pane-block">
                <span className="mini-eyebrow">AUDIT INTEGRITY</span>
                <h3>Verifiable Provenance Chains</h3>
                <p>
                  Every candidate detection is immutably linked to the raw audio snippet, model version, timestamp, and
                  reviewer signature, satisfying TNFD and CSRD ESRS E4 assurance requirements.
                </p>
                <div className="governance-badge-box">
                  <span className="badge-item">✓ TNFD v1.0 Aligned</span>
                  <span className="badge-item">✓ CSRD ESRS E4 Ready</span>
                  <span className="badge-item">✓ CC BY-NC-SA Compatible</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "pilot" && (
          <div className="tab-pane">
            <div className="pane-grid">
              <div className="pane-block">
                <span className="mini-eyebrow">STANDARDIZED METHODOLOGY</span>
                <h3>Reproducible Field PAM Protocol</h3>
                <p>
                  Our pilot protocol standardizes sensor elevation, microphone gain, schedule schedules (dawn/dusk peak
                  sampling), and acoustic index computation across all deployment zones.
                </p>
                <div className="protocol-steps">
                  <div className="step-item">
                    <strong>Phase 1: Site Stratification</strong>
                    <span>Habitat characterization, baseline noise survey, GPS geofencing.</span>
                  </div>
                  <div className="step-item">
                    <strong>Phase 2: 30-Day Continuous Ingestion</strong>
                    <span>Passive acoustic monitoring capturing 50–100+ verified sample WAVs.</span>
                  </div>
                  <div className="step-item">
                    <strong>Phase 3: Dual Verification</strong>
                    <span>BirdNET ML inference backed by qualified ornithological review.</span>
                  </div>
                </div>
              </div>

              <div className="pane-block">
                <span className="mini-eyebrow">PARTNER COLLABORATION</span>
                <h3>Certified Ecological Review</h3>
                <p>
                  All pilot datasets undergo secondary validation by an independent credentialed bioacoustics researcher
                  or ornithologist before final report generation.
                </p>
                <a
                  className="secondary"
                  href="mailto:rodrigo@listening.bio?subject=Request%20Pilot%20Protocol%20Specification"
                >
                  Download Pilot Protocol PDF <span>↗</span>
                </a>
              </div>
            </div>
          </div>
        )}

        {activeTab === "protocol" && (
          <div className="tab-pane">
            <div className="pane-grid">
              <div className="pane-block">
                <span className="mini-eyebrow">COMMERCIAL ASSURANCE</span>
                <h3>Standard Enterprise SOW & Liability</h3>
                <p>
                  Turnkey master service agreements (MSA) with defined service level agreements (SLAs), professional
                  indemnity coverage, and transparent milestone-based deliverables.
                </p>
                <ul className="check-list">
                  <li>Clear fixed-fee pilot packages ($3,500 – $10,000).</li>
                  <li>Defined delivery SLAs (under 48h turn-around for automated inference).</li>
                  <li>Standard non-disclosure agreements (NDA) and confidentiality guarantees.</li>
                </ul>
              </div>

              <div className="pane-block">
                <span className="mini-eyebrow">TARGET ECONOMICS</span>
                <h3>Transparent Service Margin</h3>
                <p>
                  Cost structure built on high-efficiency cloud batch inference, eliminating 70% of traditional field
                  survey overhead while maintaining 80%+ gross margin for software reporting.
                </p>
                <div className="margin-card">
                  <div className="margin-row">
                    <span>Traditional Field Survey:</span>
                    <strong className="high-cost">$15,000+ / site season</strong>
                  </div>
                  <div className="margin-row">
                    <span>listening.bio Continuous:</span>
                    <strong className="low-cost">$3,500 / site season</strong>
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
