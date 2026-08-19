# Controlled Enterprise Outreach SOP

This procedure governs research, drafting, demonstrations, and follow-up for
Listening.bio. It is not an authorization for autonomous cold-email sending.

## Authority boundary

An agent may:

- Research organizations and cite authoritative public sources.
- Draft account notes, routing inquiries, and follow-ups.
- Prepare a demonstration from public or client-authorized audio.
- Record campaign status and unanswered questions.

An agent may not:

- Guess a person's identity, title, address, project, or regulatory need.
- Send a new enterprise campaign without Rodrigo's immediate approval.
- Upload client audio without written authorization and handling instructions.
- Describe model candidates as confirmed observations.
- Promise pricing, savings, performance, compliance, approval, or turnaround.
- Create fake case studies, reviewers, deployments, customers, or results.

Existing partner follow-up automation is governed separately by its approved
recipient list and message limits. It does not authorize enterprise prospecting.

## 1. Account research

1. Start with an account from `POTENTIAL-CLIENTS-AND-TARGET-LIST.md`.
2. Verify the current organization and relevant program on its official site.
3. Record the source URL and date in `enterprise/account-research.csv`.
4. Verify a named person only from an authoritative public source. Otherwise use
   the official contact route and request routing.
5. Check the sent log before drafting any follow-up.

## 2. Message approval

1. Use `enterprise/SAFE-OUTREACH-SEQUENCES.md`.
2. Replace bracketed text only with sourced facts.
3. Check every statement against `enterprise/CLAIM-REGISTER.md`.
4. Present the final recipient, subject, body, sources, and reason for contact to
   Rodrigo.
5. Send only after explicit approval for that message or approved batch.

Default to asynchronous written coordination. Do not ask for a call in the first
message.

## 3. Demonstration intake

Before accepting prospect audio, obtain written confirmation of:

- Authority to share and process the files
- Intended evaluation purpose
- Location and sensitive-species handling rules
- Human-speech/privacy expectations
- Retention and deletion date
- Whether results may be discussed or published

Public and synthetic inputs remain labeled as such.

## 4. Evidence draft workflow

The application flow is:

1. `POST /audio-files/upload`
2. `POST /processing-jobs/{job_id}/run`
3. Review model candidates in the application
4. Export source-linked data or framework-informed drafts

Available draft exports include:

- `GET /exports/evidence-package.md?project_id={project_id}`
- `GET /exports/tnfd-evidence-draft.json?project_id={project_id}`
- `GET /exports/esrs-e4-evidence-draft.json?project_id={project_id}`

For a metadata-only demonstration that creates no detections:

```bash
python scripts/generate_demo_evidence_package.py recording.wav \
  --source-kind client_authorized \
  --output-dir work/evidence-draft
```

The deliverable must state that candidates are unreviewed and that the package is
not a disclosure, certification, assurance opinion, regulatory submission, or
compliance determination.

## 5. Pilot proposal gate

Do not issue a commercial statement of work until the enterprise-readiness gates
in `docs/enterprise-readiness-playbook.md` are resolved for the engagement,
including reviewer, permissions, protocol, data terms, insurance, acceptance
criteria, and measured cost assumptions.

## 6. Campaign records

For every action, record:

- Account and official source
- Recipient verification method
- Approval date
- Exact message sent
- Timestamp and channel
- Reply category
- Follow-up due date
- Demo input authorization and deletion date

No response is not consent. Stop after the approved cadence and never reply to a
bounce, automated acknowledgment, unsubscribe request, or do-not-reply address.
