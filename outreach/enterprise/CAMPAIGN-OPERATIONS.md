# Controlled Campaign Operations

## Connected channel

- Sender: `rodrigo@listening.bio`
- Provider: Hostinger Mail API
- Sent messages are retained in the mailbox Sent folder.
- Campaign owner: Rodrigo Castro

No mailbox credential, token, or provider resource identifier belongs in this
repository.

## Scheduled review

Codex automation `listening-bio-outreach-follow-up` runs at 9:00 AM Eastern,
Monday through Friday.

It may:

- Monitor the existing partner and grant threads for genuine human replies.
- Apply the previously approved acknowledgment and partner-follow-up rules.
- On Mondays, prepare no more than two sourced enterprise routing inquiries.
- Report authentication, deliverability, or processing problems.

It may not:

- Send a new enterprise message without recipient-specific approval.
- Import scraped, purchased, inferred, or non-consenting contacts.
- Submit contact forms automatically.
- Run a bulk campaign from the regular mailbox.
- Make claims outside `CLAIM-REGISTER.md`.

## Campaign states

1. `RESEARCH`: account-level fit and official route are being checked.
2. `DRAFT`: a source-backed routing inquiry is ready for review.
3. `APPROVED`: Rodrigo approved the exact recipient and message.
4. `SENT`: the message was sent and recorded in `../SENT-LOG.md`.
5. `REPLIED`: a genuine human response needs review.
6. `FOLLOW_UP_DUE`: one follow-up may be drafted under the approved cadence.
7. `CLOSED`: opted out, declined, invalid route, or cadence completed.

## Hostinger Reach boundary

Hostinger Reach should be used only for recipients who have affirmatively
subscribed or otherwise supplied a documented marketing permission. Cold
enterprise routing inquiries remain individual, approval-based messages from the
mailbox. Before a Reach campaign is activated, verify the sending domain's SPF,
DKIM, and DMARC status and review the exact audience.

## Immediate queue

- NextEra Energy Resources: official routing inquiry, draft only.
- WSP USA: official contact-form routing inquiry, draft only.
- ERM: official service-contact routing inquiry, draft only.
- Pachama / Carbon Direct: re-qualify the current organization before drafting.

