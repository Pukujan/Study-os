# Interview Source Registry

Status: proposed source-control record  
Verified: 2026-09-03  
Machine-readable registry: `datasets/interview-evidence/source-registry.json`

## Purpose

This registry answers a narrower question than the interview-evidence plan: **which sources may Study OS use, for what purpose, and with what evidence strength?**

It deliberately separates:

- repository/software license;
- rights in the underlying dataset/content;
- provenance quality;
- evidence that a question actually appeared in an interview;
- permission to ingest or transform content;
- usefulness for reproducible learning evaluation.

A public GitHub repository is not automatically an open dataset. A repository license does not automatically grant rights to third-party content collected into that repository.

## Current decisions

| Source | Class | Verified license/status | Occurrence value | Study OS decision |
| --- | --- | --- | --- | --- |
| AIMLInterviews | C open curated | MIT | Contextual/expert, not frequency | **Approved open ingest** |
| Outcome School AI Engineering Interview Questions | C open curated | Apache-2.0 | No established occurrence signal | **Approved open ingest** |
| Outcome School Machine Learning Interview Questions | C open curated | Apache-2.0 | No established occurrence signal | **Approved open ingest** |
| ML Systems Interview Bench | D open synthetic | Apache-2.0 | None by design | **Approved open ingest** |
| ML-InterviewQs | C open curated | MIT | No established occurrence signal | **Approved open ingest** |
| Kaggle SWE Interview Questions (250) | C open curated | MIT on dataset page | Weak/no per-question provenance | **Approved with provenance warning** |
| Kaggle ML & DS Question Bank (1,000+) | C open curated | MIT on dataset page | Weak/no per-question provenance | **Approved with provenance warning** |
| CodeJeet | B occurrence aggregate | GPL-3.0 repo; LeetCode-derived data | Company-tag/frequency signal | **Reference only pending rights review** |
| hxu296 LeetCode company-wise 2022 | B occurrence aggregate | MIT repo; LeetCode-derived data | Historical company-tag signal | **Reference only pending rights review** |
| snehasishroy company-wise 2026 | B occurrence aggregate | No license detected; LeetCode-derived | Recent company-tag/frequency signal | **Reference only; no bulk ingest** |
| InterviewDrip | A collection methodology | MIT software only | Stronger when source-linked candidate report exists | **Methodology/reference only; no automated LeetCode collection** |
| Hello Interview | E external restricted | Proprietary; personal/noncommercial access | Potentially strong community-report signal | **Manual/private source reference only** |
| KodeKloud | E external restricted | Proprietary; personal/noncommercial educational access | Not interview-occurrence evidence | **Manual/private source reference only** |

## Why the LeetCode-derived sources are not in the open-ingest bucket

CodeJeet is GPL-3.0 as a repository and states that its company-wise question data is sourced from `liquidslr/interview-company-wise-problems`. The upstream repositories describe the data as LeetCode company-tag/question data. Separately, current LeetCode Terms prohibit crawling/scraping the service and restrict service content.

Therefore Study OS must not infer:

> repository license = clean license to the upstream LeetCode-derived dataset.

Until rights are clearer, these sources can inform source discovery and manual research, but they are not approved as a mirrored Study OS corpus.

The same restriction applies more strongly to the 2026 `snehasishroy` snapshot because no repository license was detected in the verified repository page and its README describes premium-authenticated scraping tooling.

## Why InterviewDrip is useful but not an open interview dataset

InterviewDrip is valuable as a provenance pattern. It extracts structured interview observations and preserves the original source URL.

Its own README explicitly distinguishes the MIT-licensed software from scraped candidate posts, which remain their authors' content, and advises against publishing a verbatim scraped dataset. It also notes that its use of LeetCode's unofficial public GraphQL endpoint remains subject to LeetCode Terms.

Study OS should copy the **evidence discipline**, not assume ownership of the collected posts:

```text
candidate report
    -> source URL
    -> company / role / round / date when stated
    -> normalized competency observations
    -> confidence / self-report label
```

Manual, source-linked observations may later be added where allowed. Automated LeetCode collection is not approved by this registry.

## Open corpus approved for the first experiment

The first reproducible Study OS corpus should start from sources whose license and source status are clean enough to version locally:

1. AIMLInterviews — MIT.
2. AI Engineering Interview Questions — Apache-2.0.
3. Machine Learning Interview Questions — Apache-2.0.
4. ML Systems Interview Bench — Apache-2.0, explicitly synthetic.
5. ML-InterviewQs — MIT.
6. Kaggle SWE Interview Questions — MIT, with weak occurrence provenance label.
7. Kaggle ML & DS Question Bank — MIT, with weak occurrence provenance label.

These sources are sufficient to test **Study OS learning behavior** without claiming that their distributions represent real hiring frequency.

## External sources remain useful

Hello Interview and KodeKloud are still useful to the learner, but they serve a different purpose.

For a task opened from an external source, Study OS may retain learner-owned evidence such as:

- source URL/reference;
- minimal task metadata supplied or observed within permitted use;
- learner attempt;
- failure signature;
- assistance level;
- representation/intervention;
- learner explanation;
- transfer and retention outcome.

The current registry does **not** approve bulk scraping, cloning, or systematic derivative-dataset generation from those commercial services.

## Evidence interpretation rules

### Real-interview occurrence

Only source-linked candidate reports or explicit occurrence aggregates may increase an interview-occurrence prior. Even then:

- candidate reports remain self-report;
- company tags are not verified company policy;
- recency/frequency must retain source and observation date;
- no source may be silently upgraded to ground truth.

### Curriculum coverage

Open curated banks can establish that a competency is worth representing in the corpus, but they cannot by themselves establish how frequently employers test it.

### Learning effectiveness

No external dataset proves Study OS works.

The adaptive-learning claim still requires prospective learner episodes:

```text
baseline attempt
-> failure classification
-> intervention
-> retry
-> assistance fade
-> unaided check
-> changed-surface transfer
-> delayed retention
```

## Next engineering step

Do **not** define the final canonical ingestion schema yet.

Next:

1. fetch a small sample from each approved open-ingest source;
2. preserve source commit/version/hash and license evidence;
3. inspect real field shapes and content granularity;
4. identify the smallest common normalization that loses no important provenance;
5. only then propose a versioned Study OS interview-task/evidence schema.

This order prevents the schema from being invented from assumptions before seeing the actual data.
