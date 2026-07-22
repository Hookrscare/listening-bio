import { useMemo, useRef, useState } from "react";
import { track } from "../../lib/analytics";

const API_BASE = import.meta.env.VITE_API_BASE ?? "https://api.listening.bio";
const CONTACT_EMAIL = "rodrigo@listening.bio";

const ORG_TYPES = [
  "University",
  "Nonprofit",
  "Public agency",
  "Land trust",
  "Fiscal sponsor",
  "Park / green-space",
  "Other",
];

const ROLES = [
  "Lead applicant",
  "Scientific collaborator",
  "Site partner",
  "Funder",
  "Other",
];

type Status =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "success" }
  | { kind: "error"; message: string };

interface Errors {
  name?: string;
  email?: string;
  role?: string;
}

function isEmail(v: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
}

export function Contact() {
  const [role, setRole] = useState<string>("");
  const [status, setStatus] = useState<Status>({ kind: "idle" });
  const [errors, setErrors] = useState<Errors>({});
  const startedRef = useRef(false);
  const startTimeRef = useRef<number>(Date.now());
  const formRef = useRef<HTMLFormElement>(null);

  const onFirstInteraction = () => {
    if (!startedRef.current) {
      startedRef.current = true;
      startTimeRef.current = Date.now();
      track("contact_form_started");
    }
  };

  const mailtoFallback = useMemo(() => {
    const subject = encodeURIComponent("Listening.bio pilot partnership");
    return `mailto:${CONTACT_EMAIL}?subject=${subject}`;
  }, []);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const data = new FormData(form);

    // Honeypot + time-trap spam protection.
    if ((data.get("company_website") as string)?.length) return;
    if (Date.now() - startTimeRef.current < 1200) {
      setStatus({
        kind: "error",
        message: "Please take a moment and try again.",
      });
      return;
    }

    const name = (data.get("name") as string)?.trim() ?? "";
    const email = (data.get("email") as string)?.trim() ?? "";
    const selectedRole = (data.get("role") as string) ?? "";

    const nextErrors: Errors = {};
    if (!name) nextErrors.name = "Please enter your name.";
    if (!email || !isEmail(email))
      nextErrors.email = "Please enter a valid email address.";
    if (!selectedRole) nextErrors.role = "Please choose a partnership role.";
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;

    const payload = {
      name,
      organization: (data.get("organization") as string) ?? "",
      email,
      organization_type: (data.get("organization_type") as string) ?? "",
      partnership_role: selectedRole,
      site_area: (data.get("site_area") as string) ?? "",
      monitoring_goal: (data.get("monitoring_goal") as string) ?? "",
      equipment_staff: (data.get("equipment_staff") as string) ?? "",
      project_period: (data.get("project_period") as string) ?? "",
      context: (data.get("context") as string) ?? "",
      source: "listening.bio",
    };

    setStatus({ kind: "submitting" });
    try {
      const res = await fetch(`${API_BASE}/contact-enquiries`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`Server responded ${res.status}`);
      setStatus({ kind: "success" });
      track("contact_form_submitted", { role: selectedRole });
      form.reset();
      setRole("");
    } catch {
      setStatus({
        kind: "error",
        message:
          "We could not reach the server. You can email us directly instead.",
      });
    }
  };

  return (
    <section className="contact" id="contact" aria-labelledby="contact-heading">
      <p className="eyebrow">Start a conversation</p>
      <h2 id="contact-heading">What could your landscape tell you?</h2>

      <div className="contact-grid">
        <div>
          <p className="statement-copy">
            Listening.bio is looking for one eligible lead organization, one
            scientific collaborator, and one urban green-space partner for an
            initial acoustic biodiversity pilot.
          </p>
          <p className="contact-note">
            No ecological claim will be based solely on automated model output.
          </p>
          <p className="contact-note">
            Prefer email?{" "}
            <a href={mailtoFallback} style={{ color: "var(--lime)" }}>
              {CONTACT_EMAIL}
            </a>
          </p>
        </div>

        <form
          className="contact-form"
          ref={formRef}
          onSubmit={handleSubmit}
          onFocus={onFirstInteraction}
          noValidate
          aria-describedby="contact-status"
        >
          {/* Honeypot: hidden from users, tempting to bots. */}
          <div className="honeypot" aria-hidden="true">
            <label htmlFor="company_website">Company website</label>
            <input
              id="company_website"
              name="company_website"
              type="text"
              tabIndex={-1}
              autoComplete="off"
            />
          </div>

          <div className="field">
            <label htmlFor="c-name">Name *</label>
            <input id="c-name" name="name" type="text" autoComplete="name" />
            {errors.name && <span className="err">{errors.name}</span>}
          </div>
          <div className="field">
            <label htmlFor="c-org">Organization</label>
            <input
              id="c-org"
              name="organization"
              type="text"
              autoComplete="organization"
            />
          </div>
          <div className="field">
            <label htmlFor="c-email">Email *</label>
            <input id="c-email" name="email" type="email" autoComplete="email" />
            {errors.email && <span className="err">{errors.email}</span>}
          </div>
          <div className="field">
            <label htmlFor="c-orgtype">Organization type</label>
            <select id="c-orgtype" name="organization_type" defaultValue="">
              <option value="" disabled>
                Select…
              </option>
              {ORG_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <fieldset
            className="field full"
            style={{ border: 0, padding: 0, margin: 0 }}
          >
            <legend
              style={{
                padding: 0,
                marginBottom: 8,
                color: "var(--muted)",
                font: "500 0.68rem/1 ui-monospace, monospace",
                textTransform: "uppercase",
              }}
            >
              Partnership role *
            </legend>
            <div className="role-options">
              {ROLES.map((r) => (
                <label key={r} className="review-options" style={{ margin: 0 }}>
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 6,
                      padding: "8px 12px",
                      border: "1px solid var(--line)",
                      borderRadius: 3,
                    }}
                  >
                    <input
                      type="radio"
                      name="role"
                      value={r}
                      checked={role === r}
                      onChange={() => {
                        setRole(r);
                        track("pilot_partner_role_selected", { role: r });
                      }}
                    />
                    {r}
                  </span>
                </label>
              ))}
            </div>
            {errors.role && <span className="err">{errors.role}</span>}
          </fieldset>

          <div className="field">
            <label htmlFor="c-site">Site or geographic area</label>
            <input id="c-site" name="site_area" type="text" />
          </div>
          <div className="field">
            <label htmlFor="c-period">Preferred project period</label>
            <input id="c-period" name="project_period" type="text" />
          </div>
          <div className="field full">
            <label htmlFor="c-goal">Monitoring goal</label>
            <input id="c-goal" name="monitoring_goal" type="text" />
          </div>
          <div className="field full">
            <label htmlFor="c-equip">Available equipment or staff</label>
            <input id="c-equip" name="equipment_staff" type="text" />
          </div>
          <div className="field full">
            <label htmlFor="c-context">Additional context</label>
            <textarea id="c-context" name="context" />
          </div>

          <p
            className="contact-note full"
            style={{ marginTop: 0 }}
          >
            By submitting, you consent to Listening.bio contacting you about a
            potential pilot. We do not collect recordings, notes, or sensitive
            coordinates through this form.
          </p>

          <div
            className="form-status full"
            id="contact-status"
            role="status"
            aria-live="polite"
          >
            {status.kind === "success" && (
              <span className="success">
                Thank you — we’ll be in touch about the pilot.
              </span>
            )}
            {status.kind === "error" && (
              <span className="error">
                {status.message}{" "}
                <a href={mailtoFallback} style={{ color: "var(--lime)" }}>
                  Email us instead
                </a>
                .
              </span>
            )}
          </div>

          <div className="full">
            <button
              type="submit"
              className="primary"
              disabled={status.kind === "submitting"}
            >
              {status.kind === "submitting" ? "Sending…" : "Discuss the pilot"}
              <span aria-hidden="true">↗</span>
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}
