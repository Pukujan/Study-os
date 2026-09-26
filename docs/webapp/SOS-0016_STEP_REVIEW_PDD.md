# SOS-0016 learner step review: product definition (A8)

Status: proposed contract for InferHub A8-exec; no product implementation in A8. Owner: issue #126, parent #82, dependencies none recorded. Scope: product/UI + evaluation + schema/data specification, within the accepted D017/D018 web beta. Research Gate R0 and evidence policy do not change.

## Learner problem and outcome

After a sliding-window step changes how a box or index is explained, the learner needs to say both how useful that particular presentation was and *why*. The current thumbs control sends a positive rating immediately and only offers optional typed text behind the negative/Other path. That loses the distinction between an accidental tap and a considered review, and between a useful explanation with one wrong detail and an entirely unhelpful one. A review of `position` must continue to name `position` after chat regenerates its presentation.

**Target:** one optional review form on the learner player step: choose exactly one of 1, 2, 3, 4, 5; type what was right, wrong, or unclear; press Submit. A draft never writes. The form permits a concise reason but rejects whitespace-only input. A review can be submitted more than once as a new event when the learner deliberately starts a new review. The stored history is append-only. Numeric opinion and typed rationale are `self_reported` UX feedback, not an answer score, mastery claim, or `learn.*` evidence.

## Research and limits (sources inspected 2026-09-25)

- Five ordered response options are a common way to capture attitudes/opinions; Qualtrics explicitly describes five-point Likert choices and their limits. This motivates an ordered 1-5 *opinion* control, not a psychometrically validated Study OS scale or an interval measure. [Qualtrics, Likert scales](https://www.qualtrics.com/experience-management/research/likert-scale/).
- A concrete learning-product precedent is Coursera's [Learning How to Learn course page](https://www.coursera.org/learn/learning-how-to-learn): its published course data pairs `reviewRating` (best rating 5) with `reviewBody`. This shows the score-plus-written-review pattern, but its unit is a whole course, not a Study OS step, and it does not establish the right completion burden for this learner.
- Closed and open questions elicit different information. Pew reports that offered categories materially changed responses compared with an open question in one survey. A short typed why can expose a failure a fixed rating cannot name, but that study does not establish that requiring text improves learning or review completion. [Pew Research Center, Writing Survey Questions](https://www.pewresearch.org/writing-survey-questions/).
- Open questions impose effort; the GOV.UK design system cautions that people can find them difficult, recommends clear labels and simple prompts, and says placeholder text is not a label. Ask one brief why question with an explicit label, a 500-character limit, and no minimum word count. [GOV.UK, Textarea](https://design-system.service.gov.uk/components/textarea/).
- A submit action is an intentional write boundary. GOV.UK documents submit button semantics and accidental double-click prevention; client disabling is useful but cannot replace server idempotency. [GOV.UK, Button](https://design-system.service.gov.uk/components/button/); [Stripe, Idempotent Requests](https://docs.stripe.com/api/idempotent_requests).
- Append-only records preserve history but require explicit concurrency, privacy and read-model decisions. Microsoft describes these tradeoffs for event sourcing. Study OS only needs an append-only UX table here, not a general event-sourcing framework. [Microsoft, Event Sourcing pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing); [Study OS data policy](../DATA_POLICY.md).

## Scope and tradeoffs

| Decision | A8 contract | Reason / limit |
| --- | --- | --- |
| Storage | Keep `ux.feedback` as the append-only review record; add only what replay/identity requires | Preserve existing rows and avoid a parallel canonical review store. Existing `like`/`dislike` rows remain historical, not silently mapped to numbers. |
| Rating | Required integer 1-5, ordered from least to most useful, with visible endpoint labels | Five choices add resolution; they do not measure correctness or mastery. |
| Why | Required nonblank typed reason at Submit, no arbitrary word threshold | Alex requested typed why; a short statement is sufficient. This adds friction, so the review itself stays optional and completion should be observed before changing policy. |
| Write | Explicit Submit only; rating/text edits remain client-side drafts | Prevent accidental immediate positive sends. |
| Retry | One stable idempotency key per intended Submit; exact replay returns original receipt, a changed payload with the same key is rejected | Network retries and double-clicks cannot create duplicate rows. A fresh key means a deliberate new append. |
| Identity | Server binds authenticated subject + session + current step/variant; presentation version is context, not identity | A re-render preserves step and draft; a later step/variant must not inherit a stale draft. |
| Decision record | The committed `ux.feedback` row is the review decision record with rating, scrubbed why, target, presentation version, key, timestamp | Do not write a separate `learn.*` event or derived judgment. |
| Other surfaces | Decomposer review and tutor-message feedback remain separate | #126 targets the learner player step only. No broad feedback migration in this atomic. |

Out of A8: product code, Playwright/vision gate, live InferHub calls, chat re-render polish, pet/mascot, generalized surveys, analytics changes beyond making numeric rows readable. Those are later executor/verification slices. This spec and its tests do not claim the review is shipped.

## Done when for A8-exec

The player shows an accessible five-choice step review with labeled typed why and Submit; rating/text changes make no request. The API validates and binds the step/variant, persists the scrubbed rationale and numeric choice append-only, rejects invalid/stale submissions, and handles replay and concurrent double-submit with one logical effect. After regeneration, the same step can be reviewed with the new presentation version without moving progress. The synthetic A2A roleplay records a review beside the pinned golden path and no review enters `learn.*`. RED tests in the TDD become green. Later Playwright/vision and live InferHub gates remain separate.
