# Research Foundations

Status: **research basis for v0.1; not proof of Study OS effectiveness**

Study OS begins from a narrow question: can an AI-assisted learning system detect where a learner is failing to translate between representations of a technical concept, change the representation or learning operation, and then measure whether the change improves unaided performance, transfer, and retention?

The first domain is DSA in Python. The first longitudinal participant is `subject-001`.

## Why this problem matters

### 1. Expert explanations can hide procedural subgoals

Programming experts automate low-level procedural knowledge that novices still need made explicit. Research on subgoal-labeled worked examples in introductory programming found improved early assessment performance and lower failure/withdrawal rates for learners receiving subgoal-oriented instruction. This directly supports Study OS's interest in expanding compressed expert explanations into learner-visible intermediate steps.

Source:
- Margulieux, Morrison, & Decker (2020), *Reducing withdrawal and failure rates in introductory programming with subgoal labeled worked examples*. International Journal of STEM Education. https://doi.org/10.1186/s40594-020-00222-7

### 2. Worked examples help novices, but assistance should fade

Cognitive-load research has repeatedly found worked examples effective for novice skill acquisition because they reduce unproductive search and allow attention to be spent on understanding solution procedures. As expertise increases, excessive guidance can become unnecessary or harmful; assistance should fade toward independent problem solving.

Sources:
- van Gog, Paas, & Sweller (2010), *Cognitive Load Theory: Advances in Research on Worked Examples, Animations, and Cognitive Load Measurement*. Educational Psychology Review. https://doi.org/10.1007/s10648-010-9145-4
- Renkl-related review context summarized in: *Conditions for Effective Learning from Erroneous Examples: A Systematic Review* (2025). https://doi.org/10.1007/s10648-025-10071-x

Study OS implication: representations and hints are scaffolds, not permanent accommodations. The system must measure when they can be removed.

### 3. Visualization is not enough; active engagement matters

Program and algorithm visualizations have mixed results when learners merely watch them. A classroom study comparing prediction with visualization against viewing with instructor commentary found substantially higher active engagement in the prediction condition and faster post-test problem solving, although average post-test scores were not significantly different.

Source:
- Banerjee, Murthy, & Iyer (2015), *Effect of active learning using program visualization in technology-constrained college classrooms*. Research and Practice in Technology Enhanced Learning. https://doi.org/10.1186/s41039-015-0014-0

Study OS implication: figures, flowcharts, animations, and state traces should be interactive learning operations: predict, explain, reconstruct, alter, debug, or derive. Passive viewing is not the target behavior.

### 4. Multiple representations can help, but more is not automatically better

A 2024 systematic review/meta-analysis of more than two external representations in STEM found small average performance benefits but high heterogeneity. Additional representations can also increase cognitive load, redundancy, and confusion, particularly for learners with low prior knowledge.

Source:
- *The More the Better? A Systematic Review and Meta-Analysis of the Benefits of More than Two External Representations in STEM Education* (2024). Educational Psychology Review. https://doi.org/10.1007/s10648-024-09958-y

Study OS implication: do not display every modality simultaneously. Representation selection is an experimental variable. Prefer the minimum representation set that resolves the observed bottleneck.

### 5. Retrieval and spacing are required if we care about durable learning

Immediate fluency is not sufficient evidence of learning. Reviews of retrieval practice and spacing show that retrieving knowledge after study can improve long-term retention, and spaced retrieval supports durable learning across domains.

Sources:
- Carpenter, Pan, & Butler (2022), *The science of effective learning with spacing and retrieval practice*. Nature Reviews Psychology. https://doi.org/10.1038/s44159-022-00089-1
- McDermott (2021), *Practicing Retrieval Facilitates Learning*. Annual Review of Psychology. https://doi.org/10.1146/annurev-psych-010419-051019
- Roediger & Butler (2011), *The critical role of retrieval practice in long-term retention*. Trends in Cognitive Sciences. https://doi.org/10.1016/j.tics.2010.09.003

Study OS implication: `self_reported_understanding` and immediate success are separate from delayed reconstruction and transfer.

### 6. Carefully structured AI tutoring can improve learning; generic chat is not enough

A 2025 randomized controlled trial in undergraduate physics found greater learning gains in less median time with a carefully designed AI tutor than with an in-class active-learning condition. Importantly, the researchers report that a system prompt alone was not reliable enough to scaffold multi-part problems; the platform imposed sequential structure around the model. They also caution against assuming AI tutoring will dominate in every context, especially higher-order synthesis.

Source:
- Kestin et al. (2025), *AI tutoring outperforms in-class active learning: an RCT introducing a novel research-based design in an authentic educational setting*. Scientific Reports. https://doi.org/10.1038/s41598-025-97652-6

Study OS implication: pedagogy must live in deterministic orchestration, state, assessments, and constraints—not only in an LLM system prompt.

### 7. AI-assisted programming creates a specific need for manual comprehension and debugging

Recent programming-education research identifies a tension: GenAI can accelerate coding and explanation, while over-reliance can reduce opportunities to develop programming logic, debugging, and independent problem solving. One 2025 study found students had substantially greater difficulty correcting LLM-generated flawed code than completing conventional programming tasks, reinforcing the importance of technical scrutiny and foundational understanding.

Sources:
- *Literature Review on the Integration of Generative AI in Programming Education* (2025), International Journal of Artificial Intelligence in Education. https://doi.org/10.1007/s40593-025-00524-3
- *Integrating Generative AI into Programming Education: Student Perceptions and the Challenge of Correcting AI Errors* (2025). https://doi.org/10.1007/s40593-025-00496-4
- Rahe & Maalej (2025), *How Do Programming Students Use Generative AI?* https://arxiv.org/abs/2501.10091

Study OS implication: the target is not memorizing syntax for its own sake. The target is enough unaided code comprehension, state reasoning, implementation, testing, and debugging to evaluate and control AI-generated software.

## Why Subject 001 is an unusually informative first participant

This is a **design/research advantage**, not evidence that the system generalizes.

`subject-001` currently represents a useful transition state:

- prior experience is primarily JavaScript rather than formal Python study;
- Python is being learned in the context of scripting, AI, and technical projects rather than a conventional introductory course;
- AI can already be used to produce working scripts, while unaided code construction and DSA fluency remain explicit learning targets;
- the participant can articulate confusion, representation preferences, failed explanations, and breakthrough moments during live tutoring;
- the participant has a concrete incentive to develop manual comprehension because AI-generated code still must be reviewed, debugged, tested, and explained;
- repeated longitudinal sessions can produce process data rather than only pre/post outcomes.

This creates a high-information N=1 development environment: a real learner, real stakes, repeated observations, and strong introspective feedback.

It does **not** justify calling Subject 001 representative of novice programmers generally.

## N=1 can be rigorous for the individual, but generalization is separate

Single-case experimental designs are legitimate methods for asking causal questions about an intervention within a participant when repeated measurement, phase control, replication, and internal-validity safeguards are used. The What Works Clearinghouse maintains standards and review guidance for single-case designs. N-of-1 methodology also emphasizes repeated periods and within-person comparison when the goal is personalized evidence.

Sources:
- What Works Clearinghouse, Single-Case Design Technical Documentation. https://ies.ed.gov/ncee/wwc/Document/229
- WWC current standards resources. https://ies.ed.gov/ncee/wwc/Handbooks
- *Personalized (N-of-1) Trials: A Primer*. https://pmc.ncbi.nlm.nih.gov/articles/PMC8351788/

Study OS implication: optimize honestly for Subject 001 first, but label subject-specific findings as subject-specific until replicated.

## Important correction: do not build around fixed "learning styles"

The project may use visual, auditory, textual, structural, formal, and procedural representations. It must **not** claim that a learner has a fixed sensory learning style that should always be matched by instruction. Reviews find no adequate evidence for the common learning-styles matching hypothesis.

Source:
- Newton & Miah (2017), *Evidence-Based Higher Education — Is the Learning Styles 'Myth' Important?* Frontiers in Psychology. https://doi.org/10.3389/fpsyg.2017.00444

Study OS should instead ask an empirical question: **for this task, this knowledge state, and this observed failure, which representation operation improves behavior?**

## Mission

Build an instrumented learning procedure that converts AI-assisted study sessions into auditable evidence about:

1. where understanding breaks;
2. which representation or operation was attempted;
3. what changed after the intervention;
4. whether improvement survives removal of assistance;
5. whether it transfers to a changed problem;
6. whether it persists after delay.

## Vision

A learner should be able to move between:

`problem -> mental model -> state -> invariant -> algorithm -> pseudocode -> code -> debugging -> transfer`

without depending on memorized syntax or permanent AI completion.

Longer term, Study OS may become a general representation-learning engine. v0.1 makes no such claim.

## Claims explicitly NOT established

- Visual-first instruction is always superior.
- Subject 001 has a fixed visual learning style.
- More modalities cause more learning.
- LLM self-reports or learner self-reports accurately measure mastery.
- One successful explanation caused the learning gain.
- A method optimized for Subject 001 generalizes to other learners.
- DSA skill automatically transfers to job performance or interview success.
- An LLM can reliably infer learner state without behavioral validation.

These remain hypotheses or out-of-scope claims.