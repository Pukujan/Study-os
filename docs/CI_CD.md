# CI/CD Strategy

## Current operational pipeline (verified 2026-10-09 UTC)

The repository has **CI, production CD, and a new PR review artifact**:

| Trigger | GitHub Actions workflow | Verified role |
| --- | --- | --- |
| Every pull request, every push to `main` | [CI](../.github/workflows/ci.yml) | Python 3.11/3.12 validation, schema/privacy/test gate, frontend typecheck/unit/build, Playwright browser/vision gate |
| Every pull request update | [V2 interactive reviewer](../.github/workflows/v2-review-preview.yml) | Bundle one self-contained `review.html`; launch via `file://` and exercise it on 390×844 mobile and 1440×900 desktop without requests or an API; attach HTML and screenshots to the workflow run |
| Push to `main` (or manual dispatch) | [CD](../.github/workflows/cd.yml) | **Production** deployment on self-hosted gravebuster runner via Docker Compose, then localhost and public API health checks |

**To review any v2 PR revision:** open that PR → **Checks** → **V2 interactive reviewer** → latest successful workflow run → **Artifacts** → download `study-os-v2-offline-review`, unzip, double-click `review.html`. This artifact is retained 30 days, requires no node server or account, and does not touch the production database. Screenshots are in the same artifact. The preview is a narrow, isolated learning UI proof; it does not simulate login, saved sessions, or live AI calls. CI must still pass separately.

**Existing production deploy is not gated by a staging environment.** Merges to `main` currently trigger the live deploy, so do not merge for review. The desired follow-on is an independently hosted PR/staging URL with a disposable isolated database, proper auth test accounts, scoped secrets and automated smoke checks, plus a human promotion gate. That is **not currently implemented**. Respect [agent authority](AUTHORITY.md); only authorized reviewers can approve/merge.

Note: The historical Research Gate R0 strategy retained below predates the live site and **must not be interpreted as current runtime status**.

## Historical R0 decision (superseded operationally)

Study OS needs **continuous integration now** and **continuous deployment later**.

There is no production application worth automatically deploying during Research Gate R0. The deployable artifact at this stage is the reproducible research harness itself: schemas, deterministic ingest, validation, tests, and experiment records.

## CI goals

Every push to `main` and every pull request should answer:

1. Does Python tooling compile?
2. Are canonical JSON Schemas valid?
3. Do committed session records conform to their schemas?
4. Are project/agent boundary files present?
5. Is raw private transcript evidence accidentally tracked publicly?
6. Do deterministic ingest tests pass?

Workflow: `.github/workflows/ci.yml`

Local equivalent:

```bash
python -m pip install -r requirements-dev.txt
python -m compileall tools tests
python tools/validate_repo.py
python -m unittest discover -s tests -v
```

## Why CI matters here

For Study OS, a broken schema or lost provenance can corrupt the research corpus just as seriously as a broken function can corrupt software behavior. CI therefore protects both:

- software correctness;
- research/data integrity.

GitHub describes CI as frequently integrating changes while automatically building/testing them so errors are found early. GitHub Actions can run these checks on pushes and pull requests.

Reference: https://docs.github.com/en/actions/get-started/continuous-integration

## Security posture

Current minimum:

- workflow permissions default to `contents: read`;
- no repository secrets required by CI;
- raw transcript paths are ignored and checked for accidental Git tracking;
- dependencies are limited to development-time schema/YAML validation.

Future hardening after the repo stabilizes:

- Dependabot/Renovate or equivalent dependency updates;
- CodeQL if executable surface grows;
- OpenSSF Scorecard for public-repo supply-chain posture;
- pin third-party GitHub Actions to immutable commit SHAs when the workflow becomes security-sensitive;
- artifact attestations for released binaries/packages if releases are introduced.

References:
- GitHub Actions security: https://docs.github.com/en/actions/how-tos/secure-your-work
- OpenSSF Scorecard: https://openssf.org/scorecard/

## CD gate

Do not create automatic production deployment until all are true:

- Research Gate R0 passed;
- a stable application/API surface exists;
- the learner can use the system without manipulating research files manually;
- private data/storage boundaries are defined;
- authentication/authorization requirements are defined if any service receives transcripts;
- staging environment exists;
- smoke tests cover one complete learning episode;
- rollback strategy exists;
- observability exists for failed ingest/assessment/representation rendering.

At that point prefer:

`PR -> CI -> merge -> staging deploy -> smoke/eval -> explicit production promotion`

rather than immediate production deployment on every merge.

## Research-regression tests to add over time

Traditional unit tests are insufficient. Planned checks include:

- canonical DSA reference implementations pass problem fixtures;
- deterministic state traces match reference execution;
- representation render inputs preserve invariant/state semantics;
- derived events contain provenance;
- subject-specific observations cannot be promoted without explicit promotion metadata;
- hidden transfer fixtures do not leak into tutor-visible lesson content;
- schema migrations preserve old session readability;
- fixed benchmark trajectories remain reproducible across model/tooling changes.

## Frontend CI vs local Ultrafast (Refs #126)

- **Required CI for UI:** Playwright + InferHub vision (job `playwright` in `.github/workflows/ci.yml`).
- **Ultrafast is not a CI job.** Agents run a **local** Ultrafast scout before claiming FE done (`docs/AGENT_FRONTEND_QA.md`). Do not add Ultrafast / Jev crawl jobs to GitHub Actions.
- Local P0/P1 gate: `python tools/gate_ux_defect_report.py path/to/summary.json` (confidence never soft-skips).

