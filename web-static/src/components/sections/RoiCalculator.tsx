import { useState, useId } from "react";

export function RoiCalculator() {
  const [hectares, setHectares] = useState(500);
  const [sensors, setSensors] = useState(8);
  const [months, setMonths] = useState(6);
  const [sector, setSector] = useState("renewable");

  const hectaresId = useId();
  const sensorsId = useId();
  const monthsId = useId();
  const sectorId = useId();

  // Financial & Operational Modelling
  // Manual field surveyor: ~$1,200/day per surveyor + travel & report generation ($2,500 per site visit).
  // A typical manual campaign needs 4 visits per sensor zone per season.
  const manualVisitsPerSensor = months * 2;
  const manualCostPerVisit = 850;
  const manualTotalCost = Math.round(sensors * manualVisitsPerSensor * manualCostPerVisit + 4500);

  // listening.bio SaaS cost model: $49/mo/sensor + initial kit amortisation ($299/sensor over 3 yrs = $100/yr).
  const listeningBioPlatformFee = Math.round(sensors * months * 49 + sensors * 100 + 1200);

  const netSavings = Math.max(0, manualTotalCost - listeningBioPlatformFee);
  const savingsPercent = Math.round((netSavings / (manualTotalCost || 1)) * 100);
  const totalAudioHours = Math.round(sensors * months * 30 * 8); // 8 recording hrs/day
  const monitoringHoursPerManualVisit = 8;
  const manualObservationHours = sensors * manualVisitsPerSensor * monitoringHoursPerManualVisit;
  const coverageRatio = Math.max(1, Math.round(totalAudioHours / Math.max(1, manualObservationHours)));

  return (
    <section className="section roi-calculator-section" id="enterprise-roi" aria-labelledby="roi-title">
      <div className="section-header">
        <p className="eyebrow">Pilot planning scenario</p>
        <h2 id="roi-title">Explore continuous<br />monitoring <em>costs.</em></h2>
        <p className="section-deck">
          Adjust a transparent, illustrative scenario comparing episodic field visits with passive acoustic
          monitoring. Replace these assumptions with partner-approved costs before making a funding decision.
        </p>
      </div>

      <div className="roi-calculator-card">
        <div className="calculator-inputs">
          {/* Sector Selector */}
          <div className="input-group">
            <label htmlFor={sectorId}>Enterprise Industry Sector</label>
            <select
              id={sectorId}
              value={sector}
              onChange={(e) => setSector(e.target.value)}
              className="styled-select"
            >
              <option value="renewable">Renewable Energy (Wind & Solar Farms)</option>
              <option value="forestry">Forestry & Sustainable Agriculture</option>
              <option value="infrastructure">Infrastructure & Environmental Impact (EIA)</option>
              <option value="conservation">Land Trusts & Rewilding Reserves</option>
            </select>
          </div>

          {/* Hectares Slider */}
          <div className="input-group">
            <div className="slider-label-row">
              <label htmlFor={hectaresId}>Project Area</label>
              <span className="slider-value">{hectares.toLocaleString()} Hectares</span>
            </div>
            <input
              id={hectaresId}
              type="range"
              min="50"
              max="5000"
              step="50"
              value={hectares}
              onChange={(e) => {
                const h = parseInt(e.target.value, 10);
                setHectares(h);
                setSensors(Math.max(2, Math.round(h / 65)));
              }}
            />
          </div>

          {/* Sensors Slider */}
          <div className="input-group">
            <div className="slider-label-row">
              <label htmlFor={sensorsId}>Acoustic Monitoring Stations</label>
              <span className="slider-value">{sensors} Sensor Hubs</span>
            </div>
            <input
              id={sensorsId}
              type="range"
              min="2"
              max="40"
              step="1"
              value={sensors}
              onChange={(e) => setSensors(parseInt(e.target.value, 10))}
            />
          </div>

          {/* Monitoring Duration Slider */}
          <div className="input-group">
            <div className="slider-label-row">
              <label htmlFor={monthsId}>Monitoring Window</label>
              <span className="slider-value">{months} Months / Year</span>
            </div>
            <input
              id={monthsId}
              type="range"
              min="1"
              max="12"
              step="1"
              value={months}
              onChange={(e) => setMonths(parseInt(e.target.value, 10))}
            />
          </div>
        </div>

        {/* Results Matrix */}
        <div className="calculator-results">
          <div className="savings-hero-box">
            <span className="results-eyebrow">ILLUSTRATIVE COST DIFFERENCE</span>
            <div className="savings-number">${netSavings.toLocaleString()}</div>
            <span className="savings-badge">{savingsPercent}% in this editable scenario</span>
          </div>

          <div className="metrics-summary-grid">
            <div className="metric-cell">
              <span>Manual Survey Cost</span>
              <strong>${manualTotalCost.toLocaleString()}</strong>
            </div>

            <div className="metric-cell highlight">
              <span>listening.bio SaaS Cost</span>
              <strong>${listeningBioPlatformFee.toLocaleString()}</strong>
            </div>

            <div className="metric-cell">
              <span>Audio Data Captured</span>
              <strong>{totalAudioHours.toLocaleString()} hrs</strong>
            </div>

            <div className="metric-cell">
              <span>Potential recording coverage</span>
              <strong>{coverageRatio}x the assumed visit hours</strong>
            </div>
          </div>

          <div className="compliance-readiness-banner">
            <div className="compliance-icon">✓</div>
            <div>
              <strong>Evidence-package prototype</strong>
              <p>Supports provenance and review records that partners may use when preparing their own disclosures. It is not a certification or compliance determination.</p>
            </div>
          </div>

          <details className="scenario-assumptions">
            <summary>Scenario assumptions</summary>
            <p>
              Manual comparison: {manualVisitsPerSensor} visits per station at ${manualCostPerVisit.toLocaleString()}
              per visit, plus $4,500 for coordination and reporting. Platform scenario: $49 per station-month,
              $100 annual equipment allowance per station, and $1,200 for setup and reporting. Recording coverage
              assumes eight hours per station-day. Taxes, travel, scientific review, hardware purchases, and partner
              overhead may change the result.
            </p>
          </details>

          <div className="roi-actions">
            <a
              className="primary"
              href="mailto:rodrigo@listening.bio?subject=Enterprise%20ROI%20and%20TNFD%20Pilot%20Proposal"
            >
              Request a scoped pilot estimate <span>↗</span>
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
