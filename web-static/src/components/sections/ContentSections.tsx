import { track } from "../../lib/analytics";

export function Proof() {
  return (
    <section className="proof" aria-label="Current readiness">
      <article>
        <span>01 / Workflow</span>
        <strong>Functional MVP</strong>
        <p>Audio, BirdNET, provenance, review, maps, and exports.</p>
      </article>
      <article>
        <span>02 / Evidence</span>
        <strong>Real audio tested</strong>
        <p>A public environmental recording completed the full pipeline.</p>
      </article>
      <article>
        <span>03 / Next proof</span>
        <strong>Partner-led field pilot</strong>
        <p>Scientifically reviewed evidence from approved local sites.</p>
      </article>
    </section>
  );
}

export function Statement() {
  return (
    <section className="statement section" id="method">
      <div>
        <p className="eyebrow">Why this exists</p>
        <h2>
          Listen longer.
          <br />
          Claim less.
          <br />
          <em>Learn more.</em>
        </h2>
      </div>
      <div className="statement-copy">
        <p>
          Acoustic monitoring can extend observation across more hours and
          locations than point-in-time surveys. But automated predictions become
          misleading when the source, settings, confidence, and review decisions
          disappear.
        </p>
        <p>
          Listening.bio keeps the evidence chain intact, from the original WAV
          recording to every human decision.
        </p>
      </div>
    </section>
  );
}

const WORKFLOW: [string, string, string][] = [
  ["01", "Collect", "Standardized field audio"],
  ["02", "Process", "Documented BirdNET run"],
  ["03", "Preserve", "Source and model provenance"],
  ["04", "Review", "Qualified human validation"],
  ["05", "Report", "Conservative findings"],
];

export function Pilot() {
  return (
    <section className="pilot section" id="pilot" aria-labelledby="pilot-heading">
      <div className="section-head">
        <div>
          <p className="eyebrow">Proposed collaboration</p>
          <h2 id="pilot-heading">
            A focused
            <br />
            $10,000 pilot.
          </h2>
        </div>
        <p>
          Thirty days across three to five urban green-space sites, designed with
          a qualified scientific collaborator and an eligible lead partner.
        </p>
      </div>
      <div className="pilot-measures">
        <article>
          <strong>30</strong>
          <span>days</span>
        </article>
        <article>
          <strong>3–5</strong>
          <span>sites</span>
        </article>
        <article>
          <strong>50–100</strong>
          <span>WAV recordings</span>
        </article>
        <article>
          <strong>1</strong>
          <span>reviewed dataset</span>
        </article>
      </div>
      <div className="workflow" aria-label="Pilot workflow">
        {WORKFLOW.map(([n, title, copy]) => (
          <article key={n}>
            <span>{n}</span>
            <div>
              <strong>{title}</strong>
              <p>{copy}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export function Partners() {
  return (
    <section
      className="partners section"
      id="partners"
      aria-labelledby="partners-heading"
    >
      <div className="section-head">
        <div>
          <p className="eyebrow">The collaboration model</p>
          <h2 id="partners-heading">
            One pilot.
            <br />
            Four roles.
          </h2>
        </div>
        <p>
          Listening.bio is enabling infrastructure. Scientific interpretation and
          site decisions stay with qualified partners.
        </p>
      </div>
      <div className="partner-grid">
        <article>
          <span>Lead applicant</span>
          <h3>Eligible organization</h3>
          <p>
            A university, nonprofit, public agency, land trust, or fiscal sponsor
            manages the award.
          </p>
        </article>
        <article>
          <span>Scientific lead</span>
          <h3>Ecological reviewer</h3>
          <p>
            An ecologist, ornithologist, or bioacoustics researcher approves
            protocol and validation.
          </p>
        </article>
        <article>
          <span>Site partner</span>
          <h3>Landscape steward</h3>
          <p>
            A park or land manager supports access and defines the questions that
            matter.
          </p>
        </article>
        <article>
          <span>Technology partner</span>
          <h3>Listening.bio</h3>
          <p>
            We provide processing, provenance, review tools, structured exports,
            and reporting support.
          </p>
        </article>
      </div>
    </section>
  );
}

const BUDGET: [string, string][] = [
  ["Recording equipment and supplies", "$2,000"],
  ["Field collection and coordination", "$2,000"],
  ["Scientific protocol and review", "$2,500"],
  ["Engineering, processing, and data management", "$2,000"],
  ["Reporting and partner workshop", "$1,000"],
  ["Contingency", "$500"],
];

export function Budget() {
  return (
    <section className="budget section" aria-labelledby="budget-heading">
      <div>
        <p className="eyebrow">Transparent by design</p>
        <h2 id="budget-heading">
          Where the pilot
          <br />
          funding goes.
        </h2>
        <p className="budget-note">
          A deliberately small budget focused on field evidence, scientific
          quality, and reusable outputs.
        </p>
      </div>
      <div className="budget-list">
        {BUDGET.map(([label, amount]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{amount}</strong>
          </div>
        ))}
        <div className="total">
          <span>Total requested</span>
          <strong>$10,000</strong>
        </div>
      </div>
    </section>
  );
}

export function Boundary() {
  return (
    <section className="boundary section" aria-labelledby="boundary-heading">
      <p className="eyebrow">Evidence boundary</p>
      <h2 id="boundary-heading">What we will not claim.</h2>
      <div className="boundary-grid">
        <p>Automated predictions are not confirmed observations.</p>
        <p>A pilot is not comprehensive biodiversity coverage.</p>
        <p>Acoustic monitoring does not replace expert ecological surveys.</p>
        <p>Sensitive locations will not be published without review.</p>
      </div>
    </section>
  );
}

export function Closing() {
  return (
    <section className="closing" aria-label="Pilot partnerships 2026">
      <div>
        <p className="eyebrow">Pilot partnerships / 2026</p>
        <h2>
          What could your
          <br />
          landscape tell you?
        </h2>
        <p>
          We are looking for one lead applicant, one scientific collaborator, and
          one site partner ready to build credible field evidence together.
        </p>
        <a
          className="primary"
          href="#contact"
          onClick={() => track("hero_pilot_cta_clicked", { location: "closing" })}
        >
          Start the conversation <span aria-hidden="true">↗</span>
        </a>
      </div>
    </section>
  );
}
