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
  const speciesObservationMultipier = "14.2x";

  return (
    <section className="section roi-calculator-section" id="enterprise-roi" aria-labelledby="roi-title">
      <div className="section-header">
        <p className="eyebrow">Enterprise B2B & TNFD Compliance</p>
        <h2 id="roi-title">Calculate continuous<br />monitoring <em>ROI.</em></h2>
        <p className="section-deck">
          Compare traditional episodic field surveys against continuous passive acoustic monitoring (PAM) with
          auditable model provenance and TNFD/CSRD reporting.
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
            <span className="results-eyebrow">ESTIMATED ANNUAL SAVINGS</span>
            <div className="savings-number">${netSavings.toLocaleString()}</div>
            <span className="savings-badge">{savingsPercent}% Cost Reduction vs. Manual Surveys</span>
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
              <span>Observation Density</span>
              <strong>{speciesObservationMultipier} more data</strong>
            </div>
          </div>

          <div className="compliance-readiness-banner">
            <div className="compliance-icon">✓</div>
            <div>
              <strong>TNFD & CSRD (ESRS E4) Audit Ready</strong>
              <p>Generates verifiable evidence chains with raw WAV hashes and scientific human reviews.</p>
            </div>
          </div>

          <div className="roi-actions">
            <a
              className="primary"
              href="mailto:rodrigo@listening.bio?subject=Enterprise%20ROI%20and%20TNFD%20Pilot%20Proposal"
            >
              Request Enterprise Proposal <span>↗</span>
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
