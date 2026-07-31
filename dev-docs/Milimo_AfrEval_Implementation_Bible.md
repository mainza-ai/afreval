# Milimo AfrEval — Implementation Bible
### The Autonomous Context-Aware Alignment & Benchmarking Infrastructure for AI in Africa
**Version 1.0 — Source-of-truth build spec for AI-agent-driven implementation**

---

## 0. How to use this document

This is the operating spec for building Milimo AfrEval end to end. It is written to be read and executed by an AI coding agent (Claude Code, Codex, or equivalent), not just a human. Every subsystem below follows the same rule: **state the frozen harness, the mutable artifact, the instruction file, the metric, and the budget before writing a line of implementation code.** If a section doesn't have those five things defined, stop and define them before building.

The plan is organized in five parts:

1. **Core design pattern** — the "Karpathy Loop" and why it's the right substrate for AfrEval, including the multi-platform caveat and how it's resolved.
2. **Data & benchmarking substrate** — WAXAL, AfroBench, afri-fertility, and how each becomes a frozen evaluation harness.
3. **System architecture** — six subsystems, each mapped to a loop, a language, and a repo.
4. **Infrastructure & trust boundary** — sandboxing, MCP, agent-airlock-style validation, and how the loop hardens it over time.
5. **Phased build plan** — repo layout, milestones, acceptance criteria, and risk register.

---

## 1. Core design pattern: the Karpathy Loop, generalized

### 1.1 The canonical pattern

[karpathy/autoresearch](https://github.com/karpathy/autoresearch) reduces autonomous ML research to three files and a rule:

- **`prepare.py`** — a frozen, human-owned harness. Data prep, eval protocol, runtime utilities. The agent never touches this.
- **`train.py`** — the single mutable artifact. The agent rewrites architecture, hyperparameters, optimizer — anything — inside this one file.
- **`program.md`** — the agent's operating instructions, written and edited by the human, read by the agent.

The loop: modify → run for a **fixed time budget** (5 minutes wall-clock in the original) → score against **one scalar metric** (`val_bpb`, vocab-size-independent) → keep if improved, discard if not → repeat. At ~12 experiments/hour this yields ~100 experiments overnight, unattended.

The formalized version of this pattern, as the community now calls it (see [webfuse-com/awesome-autoresearch](https://github.com/webfuse-com/awesome-autoresearch)):

```
AGENT + CONSTRAINED_SCOPE + SCALAR_METRIC + FAST_VERIFICATION = AUTONOMOUS_IMPROVEMENT
```

### 1.2 The generalization that unlocks the rest of AfrEval

The base repo is ML-training-specific. But [uditgoenka/autoresearch](https://github.com/uditgoenka/autoresearch) ("Claude Autoresearch") generalizes the exact same loop into a Claude Code skill that works on **any domain with a measurable metric** — code, security audits, docs, DevOps — using `git commit → verify → keep/revert` instead of a training run:

```
LOOP (N iterations or until done):
  1. Review current state + git history + results log
  2. Pick the next change (based on what worked, what failed, what's untried)
  3. Make ONE focused change
  4. Git commit (before verification)
  5. Run mechanical verification (tests, benchmarks, scores)
  6. If improved → keep. If worse → git revert. If crashed → fix or skip.
  7. Log the result
  8. Repeat
```

This is the load-bearing insight for AfrEval: **not every subsystem is an ML training loop, but every subsystem can be a Karpathy Loop.** Tokenizer search is a training-style loop. Adversarial red-teaming of `agent-airlock` is a `git commit / revert` style loop. Context Score weight calibration is a `git commit / revert` style loop over a config file. This document specifies, for each subsystem, which flavor of the loop applies and why — see §3.

**Reference-only, not a base repo.** `uditgoenka/autoresearch` has no training code — it's markdown: a thin routing file plus per-command instruction files that tell Claude Code how to run the `git commit → verify → keep/revert` cycle on an arbitrary metric. There's no domain logic to re-engineer because there isn't a system underneath it, just an instruction pattern. Treat it exactly like the platform forks in §1.3: read it once for *how it structures* a routing file and per-command instruction files, then write AfrEval's own `program.md`/`GOAL.md` per subsystem directly (§3.2, §3.3, §3.5, §3.6) rather than adopting its plugin packaging, command surface, or marketplace listing. It doesn't compete with `karpathy/autoresearch` as a starting clone — the two solve different halves of the problem: `karpathy/autoresearch` has actual model/training code worth re-engineering (§3.1, §3.4); `uditgoenka/autoresearch` has none, it's a pattern to learn from for the four non-ML loops.

Related generalized forks worth knowing about (not required, but useful references for the agent instruction files in §3): [leo-lilinxiao/codex-autoresearch](https://github.com/webfuse-com/awesome-autoresearch) (Codex-native, resume support, lessons-across-runs), [SeeleAI/Thoth](https://github.com/webfuse-com/awesome-autoresearch) (dashboard-first, durable runs, reviewable verdicts — directly relevant to §5's audit trail requirement), [jmilinovich/goal-md](https://github.com/webfuse-com/awesome-autoresearch) (`GOAL.md` pattern for constructing a fitness function before optimizing — relevant to §3.2's Context Score calibration, where the fitness function itself is not yet known).

### 1.3 The platform caveat — resolved by re-engineering, not by forking

The base `autoresearch` repo is **single NVIDIA GPU only**, and the maintainer has explicitly said platform generalization is out of scope for the core repo, deferring it to community forks. That's the caveat flagged previously, and it is a first-class constraint for AfrEval, not a footnote — because AfrEval's entire thesis is performance under constrained/non-datacenter compute.

**Resolution approach: clone the base repo once, then re-engineer your own copy until the platform ceiling is gone.** This is not "pick a pre-built fork and depend on it." AfrEval takes zero runtime or code dependency on any third-party fork. `git clone karpathy/autoresearch` gives you a skeleton — three files and a loop discipline — and every constraint the base repo carries (CUDA-only, single mutable file scoped to a GPT training loop, `val_bpb` as the metric) gets rewritten out during re-engineering, not inherited. Once the rewrite is done it is Milimo AfrEval's own codebase; the upstream repo is a historical starting point, not a dependency to track or merge from.

Community forks ([miolini/autoresearch-macos](https://github.com/miolini/autoresearch-macos), [trevin-creator/autoresearch-mlx](https://github.com/webfuse-com/awesome-autoresearch), [jsegov/autoresearch-win-rtx](https://github.com/webfuse-com/awesome-autoresearch), [andyluo7/autoresearch](https://github.com/webfuse-com/awesome-autoresearch), [iii-hq/n-autoresearch](https://github.com/webfuse-com/awesome-autoresearch)) are useful **as technique references only** — read their diffs against upstream to see *how* each solved a specific constraint, then implement your own version of that technique inside your own clone. No code, package, or git remote from any of them enters the AfrEval tree. Specifically worth reading (not importing) before writing the device layer:

- How the MPS forks drop the hard FlashAttention-3 dependency and fall back to PyTorch's native SDPA with manual sliding-window causal masking — the technique, not the diff itself, is what you re-implement.
- How they handle MPS-specific memory/batch-size constraints (Metal has different bounds than CUDA) and optimizer-state casting.
- How the multi-GPU fork structures experiment tracking, crash recovery, and queryable orchestration once a single-machine loop needs to become a fleet-scale one — relevant later, per §3.2's requirement that Context Score calibration eventually runs continuously rather than as an overnight batch.

**Re-engineering task list for the device layer** (do this once, in `afreval-harness/`, shared by every subsystem in §3 rather than re-solved per-repo):

1. Strip the hard CUDA/FlashAttention-3 assumption out of the cloned training loop.
2. Add a device-detection module — CUDA → MPS → CPU/ONNX-mobile, in priority order, mirroring the autodetection pattern `nanochat` itself already ships, and the same shape as Milimo Quantum's own HAL (Aer CPU simulation, PyTorch MPS for QML, MLX as primary inference backend). Written from scratch, against your own harness's needs — not copied from any fork.
3. Gate the SDPA fallback and MPS-specific batch/memory handling behind that device layer, so the same `train.py`-equivalent artifact runs unmodified on whatever hardware is detected.
4. For §3.4 specifically (WAXAL-NET edge validation): the device layer must support an **explicit hardware-class assertion**, not silent autodetection-and-proceed. If a run claims to validate "beats zero-shot on low-end mobile WER," it must fail loudly if it detects it's actually running on a workstation GPU instead of the asserted target class — auto-fallback-and-continue would silently invalidate the exact claim Phase 4's acceptance criteria depends on.
5. Non-ML loops (§3.2, §3.3, §3.5 — Context Score calibration, BiasScope, agent-airlock hardening) don't need this device layer at all; they're `git commit`/revert loops over code and config, not GPU-bound training runs, and should be built directly rather than descended from the training-loop skeleton.

---

## 2. Data & benchmarking substrate

Every loop in §3 needs a **frozen harness** to score against. These three sources are that harness. None of them get modified by any agent, ever — they are the eval ground truth, versioned and pinned like a test suite.

### 2.1 WAXAL — acoustic substrate

- Source: [Waxal-Multilingual/speech-data](https://github.com/Waxal-Multilingual/speech-data), paper at [arXiv:2602.02734](https://arxiv.org/abs/2602.02734), dataset mirror at [google/WaxalNLP on Hugging Face](https://huggingface.co/datasets/google/WaxalNLP).
- Coverage: ASR portion collected via **image-prompted speech** (speakers describe an image in their native language — avoids the artificial cadence of scripted reading), captured in natural environments, each clip ≥15 seconds, with speaker age/gender/language/environment metadata tracked. Only ~10% of collected audio is transcribed (by paid local linguistic experts, using local scripts where available) — this is your ASR training/eval set. TTS portion is studio-quality, single-speaker, phonetically balanced.
- Scale: ~1,250 hours transcribed ASR, ~180-235 hours TTS (figures vary slightly by paper revision — pin the exact revision you build against), spanning 21-27 languages depending on release, 100M+ speakers represented.
- Provenance: collected via partnerships with Makerere University, University of Ghana, Digital Umuganda, Media Trust, Loud and Clear, and AIMS Senegal — useful context for any compliance/data-sovereignty conversation with African regulators, since the collection partners are themselves regional institutions.
- Use in AfrEval: frozen eval harness for the Linguistic Fidelity vector's acoustic component (WER/CER against WAXAL held-out set), and the training substrate for the WAXAL-NET-style edge ASR loop (§3.4).
- WAXAL-NET reference paper: [arXiv:2606.02375](https://arxiv.org/abs/2606.02375) — confirms the core thesis: fine-tuned compact edge models beat massively multilingual zero-shot foundation models on macro-averaged WER for spontaneous African speech, with cross-domain evaluation showing fine-tuned models generalize to out-of-distribution speech while zero-shot models only win when the test domain matches their pretraining distribution. This is your benchmark to beat, not just cite.

**2.1.1 — WAXAL acquisition & QA task list (agent-executable, Phase 0 blocking).** This is a mechanical, scriptable task — assign it directly, don't leave it as tribal knowledge:

1. **Pull by config, not by tree.** `google/WaxalNLP` on Hugging Face is organized per-language, per-task (`{lang}_asr`, `{lang}_tts`), each example already carrying a `transcription` field. Do not do a blind `tree/main` clone. For each language in the pinned set, either `load_dataset("google/WaxalNLP", "{lang}_asr")` or `snapshot_download(repo_id="google/WaxalNLP", repo_type="dataset", allow_patterns="*_asr/*.parquet", local_dir=...)` — ASR shards only, TTS excluded unless a subsystem specifically needs it.
2. **Empty/null transcription audit.** Before anything is pinned, run a pass over every pulled config counting empty or null `transcription` fields. Log the per-language rate. If any language's rate is non-trivial, filter it (`.filter(lambda x: len(x["transcription"]) > 0)`) before it enters the frozen harness — do not assume presence, verify it.
3. **Transcription-quality QA pass.** Re-transcribe a sample (or the full set, compute-budget permitting) with a second ASR pass, compute edit distance against the shipped transcription per clip, and flag/exclude high-divergence or corrupted-file rows. This is the same technique the `galsenai/WaxalNLP` community fork used to catch misaligned transcriptions and unreadable files — replicate it rather than discovering the same failure modes after scores are already pinned.
4. **Checksum and freeze.** Once steps 1-3 are done for the pinned language set, checksum the resulting filtered corpus and commit it as the Phase 0 harness artifact, per §2's "nothing downstream starts until this is versioned" rule. Record the exact HF dataset revision/commit hash pulled from, the language codes included, and the per-language pre/post-filter row counts in the harness README — this is the provenance record that makes a later Context Score defensible if anyone asks "what exactly was this model scored against."

### 2.2 AfroBench — textual/reasoning substrate

- Source: [McGill-NLP/AfroBench](https://github.com/McGill-NLP/AfroBench), leaderboard/demo at [mcgill-nlp.github.io/AfroBench](https://mcgill-nlp.github.io/AfroBench/), paper at [arXiv:2311.07978](https://arxiv.org/abs/2311.07978).
- Coverage: 64 African languages, 15 NLP tasks, 22 datasets — classification, QA, reasoning, generation. Built specifically because prior multilingual benchmarks (e.g. MEGA) exclude African languages due to data scarcity and low discoverability of existing datasets.
- **AfroBench-LITE**: the compute-constrained variant — 7 datasets, 14 languages — this is the one AfrEval should default to for routine/high-frequency certification passes, reserving full AfroBench for periodic deep audits (see §3.2's cadence design).
- Empirical findings to bake into your scorer's priors: proprietary models (GPT-4o, Gemini 1.5 Pro) lead on raw average score; among open models, Gemma 2 27B leads and beats LLaMA 3.1 70B despite ~half the parameters; fine-tuned baselines on AfroBench datasets often beat prompted general-purpose LLMs; knowledge-intensive and reasoning tasks show the largest performance gap. This directly supports the doc's Lugha-Llama citation (targeted adaptation beating scale) — build the Context Score's Linguistic Fidelity vector to reward this, not penalize smaller specialized models relative to bigger generalist ones.

### 2.3 afri-fertility — tokenization economics substrate

- Package: `afri-fertility` on PyPI (per your source doc's citation #7 — pin the exact version before building against it; treat PyPI version drift as a breaking-change risk, not a routine bump).
- Grounding paper: **"The African Language Tax"**, [arXiv:2606.24460](https://arxiv.org/html/2606.24460). Explicitly built on the methodological template of Ovcharov 2026 (which measured a ~2.5× tokenizer tax across 25 European languages) but extends it to non-Latin scripts (Ge'ez/Ethiopic, Arabic/Ajami, N'Ko), heavier agglutinative/tonal morphology, and thinner training representation — and is the first to translate the fertility gap into enterprise cost/latency/context terms, which is exactly the framing AfrEval's Structural Economics vector needs.
- Privacy/security note worth carrying into your own tooling's design: the paper states the afri-fertility tool "stores no user data and makes no network requests beyond downloading tokenizer files from the Hugging Face Hub" — match this bar for any component of AfrEval that touches enterprise-submitted models; it is a reasonable minimum privacy posture to hold the whole platform to, not just this one component.
- Source corpora: FLORES-200+, SIB-200, MAFAND-MT — all open-licensed. Confirm license compatibility with your enterprise SaaS terms before redistributing any derived scores publicly (e.g. a public "token fertility leaderboard" feature, if built, needs its own license review separate from the internal certification use).

---

## 3. System architecture: six subsystems, each a Karpathy Loop

Each subsystem below specifies: **frozen harness / mutable artifact / instruction file / metric / budget / loop flavor / language / repo.**

### 3.1 Tokenizer & vocab search loop (kills the African Language Tax at the root)

| Field | Spec |
|---|---|
| Frozen harness | `harness/tokenizer_eval.py` — loads pinned FLORES-200+/SIB-200/MAFAND-MT corpora, re-tokenizes with candidate vocab, computes CPT/BPT per language and per script (Latin/Ge'ez/N'Ko stratified, never aggregated blind) |
| Mutable artifact | `candidates/tokenizer_candidate.py` — vocab construction: BPE merge ordering, script-aware pre-tokenization, unigram vs BPE choice, vocab size, byte-fallback thresholds |
| Instruction file | `program.md`: "minimize mean fertility premium vs English across the pinned 20-language/3-script table without regressing English CPT by more than 5%. N'Ko and Ethiopic premiums are scored independently — a win on Latin script does not offset a regression on either." |
| Metric | Mean fertility premium, script-stratified (three numbers, not one) |
| Budget | Fixed wall-clock per candidate build + re-tokenize + score pass (GPU-bound for large candidate vocabs, CPU-bound for smaller ones — budget both paths) |
| Loop flavor | Training-style (base `autoresearch` pattern) |
| Language | Python |
| Repo | `afreval-tokenizer-research` |

### 3.2 Context Score calibration loop

The Context Score is AfrEval's core IP: a 0-100 composite of **Linguistic Fidelity** (WAXAL WER/CER + AfroBench task accuracy, weighted toward code-switching robustness), **Cultural Safety** (BiasScope-corrected judge output, §3.3), and **Structural Economics** (inverse of afri-fertility premium). The weighting function is per-industry (telco weights fluidity/latency, bank weights security/alignment) and today is presumably hand-set. That's a search problem.

| Field | Spec |
|---|---|
| Frozen harness | The three scoring pipelines from §2 (WAXAL WER, AfroBench-LITE, afri-fertility), deterministic and version-pinned |
| Mutable artifact | `weights/{vertical}.yaml` — the weight function + threshold per industry vertical |
| Instruction file | `GOAL.md` (per the [jmilinovich/goal-md](https://github.com/webfuse-com/awesome-autoresearch) pattern) — because unlike §3.1, the fitness function itself isn't fully known yet. First loop pass constructs the labeled-outcome dataset (models that passed and later caused incidents vs. models that held up in production); second loop pass searches weights against it. Do not skip straight to weight search before the fitness function exists — that's the mistake this pattern is specifically for. |
| Metric | Precision/recall of the weight function against incident-labeled deployment history, or a synthetic adversarial holdout if real incident data is too sparse in early operation |
| Budget | `git commit`/revert per weight-config change, N=fixed iterations per calibration run, not wall-clock |
| Loop flavor | `git commit`/revert style (generalized Karpathy Loop, per §1.2) |
| Language | Rust for the production scorer (same hot path as the zero-trust runtime, §4); Python for the search loop, calling the Rust scorer over a thin FFI or gRPC boundary |
| Repo | `afreval-context-score` (Rust core + `research/` Python search harness) |
| Cadence requirement | Re-run at minimum monthly per vertical, and immediately on any upstream frontier model release relevant to a currently-certified deployment — your own doc notes a model passing in January can drift into non-compliance by March; the calibration loop and the certification loop are not the same loop and must not be conflated (see §3.2.1) |

**3.2.1 — Certification loop vs. calibration loop, kept separate.** The calibration loop (above) tunes *how* scores are weighted. The certification loop is the actual per-model, per-deployment scoring pass run against a submitted model — this is not a search loop at all, it's a deterministic pipeline invocation, and it must be reproducible and auditable (same model + same weight config + same harness version → same score, always). Do not let an agent "optimize" the certification pipeline itself against a metric like "throughput" without an explicit accuracy-preserving constraint, or you will silently create the exact evaluation-bias failure mode your own doc describes for LLM-as-judge systems, just inside your own scorer instead of a third party's.

### 3.3 BiasScope adversarial probe discovery loop

- Grounding: BiasScope, [arXiv:2602.09383](https://arxiv.org/html/2602.09383v1) — automated detection of bias in LLM-as-a-judge evaluation. Grounding for the underlying phenomenon: **"LLM Evaluators are Biased across Languages,"** [arXiv:2607.14480](https://arxiv.org/html/2607.14480v1) — multilingual judges assign different absolute scores for semantically identical content depending on language, correlated with resource level and driven by model uncertainty on high-perplexity/underrepresented text (measured via negative log-likelihood and token-free uncertainty), with judges defaulting to artificially generous ratings under low confidence. Pairwise accuracy is structurally blind to this because it only measures relative ranking, not absolute-score drift — evaluators can clear 90%+ pairwise accuracy while showing up to a 43% acceptance-rate gap across languages under one global threshold.

| Field | Spec |
|---|---|
| Frozen harness | The LLM-judge harness + low-resource-language corpus |
| Mutable artifact | The perturbation-generation strategy (an agent-editable "attack program") |
| Instruction file | `program.md`: "maximize the induced pairwise-accuracy-vs-absolute-score-gap without the judge flagging the input as adversarial" |
| Metric | Acceptance-rate delta across languages under the fixed decision threshold (the 43%-gap figure above is your existence proof that this metric is exploitable — treat it as the number to beat, in the defensive direction, over time) |
| Budget | Fixed **number of judge API calls** per generation round, not wall-clock — this loop is cost-bound, not time-bound, since every iteration burns judge-model tokens |
| Loop flavor | `git commit`/revert style, cost-budgeted variant |
| Language | Python for agent loop + probe generation; Rust for the perturbation runtime if embedded in the same sandboxed path as §4 (keeps adversarial-input-generation code physically separated from anything near production credentials) |
| Repo | `afreval-biasscope` |

### 3.4 WAXAL-NET edge ASR fine-tuning loop

The clearest 1:1 reuse of the original autoresearch shape, and the one place where §1.3's platform resolution is non-optional, not optional.

| Field | Spec |
|---|---|
| Frozen harness | WAXAL held-out eval split, WER/CER scoring (CER tracked alongside WER — for syllabary-script languages the CER/WER ratio reveals meaningfully higher character-level accuracy than WER alone suggests, so don't drop CER even though WER is the headline number) |
| Mutable artifact | ASR fine-tune config/architecture, same "one file, agent edits it" discipline as `train.py` |
| Instruction file | `program.md`, adapted from the MLX/edge fork lineage, not the CUDA original |
| Metric | Macro-averaged WER across the 19-language WAXAL-NET set, with cross-domain OOD generalization tracked as a secondary metric (per the WAXAL-NET paper's own finding: fine-tuned models generalize better OOD, zero-shot models only win in-distribution — you want both numbers, not just headline WER, or you'll ship a model that's great on the benchmark and brittle in the field) |
| Budget | Fixed wall-clock per fine-tune run, sized for the target edge hardware class, not a datacenter GPU — if you're validating "runs on low-end mobile," the search loop needs to run on comparable compute or the result is meaningless |
| Loop flavor | Training-style, MLX/ONNX-mobile fork lineage (§1.3) |
| Language | Python for the training/search loop; export to ONNX/TFLite/Core ML for on-device; Dart/Flutter client for field data collection (image-prompted elicitation UI, matching WAXAL's own collection methodology) and on-device eval telemetry reporting |
| Repo | `afreval-waxal-net` (Python core) + `afreval-field-app` (Dart/Flutter) |

### 3.5 agent-airlock hardening loop (adversarial, against your own execution boundary)

**Dependency strategy note — this subsystem is the one deliberate exception to §1.3's "re-engineer, don't depend" rule.** `autoresearch` is a whole-system skeleton (three files defining a research-loop *pattern*) with no domain-specific hardening to preserve — re-engineering it from scratch loses nothing and gains full ownership. `agent-airlock` is the opposite case: a narrow, security-focused library where the value *is* the hardening itself — validated defended-against attack classes, edge cases already found and patched, a maintainer actively shipping CVE-style presets in reaction to real upstream MCP vulnerabilities (see the Mobile MCP `mobile_open_url` scheme-validation preset below). Reimplementing that from scratch means re-discovering the same vulnerability classes the hard way, on a system that's meant to be certifying other people's AI agents as safe. Build on it as a real dependency (forked/vendored into `afreval-airlock`, tracked against upstream releases, license-checked before vendoring) rather than re-engineering it out. Extend it for the fourth seam (§3.5's per-call reauthorization, which is genuinely unbuilt upstream) rather than rebuilding the first three.

Reference implementation to build on/against: [sattyamjjain/agent-airlock](https://github.com/sattyamjjain/agent-airlock) — a deny-by-default, Pydantic-based, in-process, zero-core-deps contract/type-checker layer for AI agent tool calls, positioned to sit beneath MCP gateways/firewalls, with framework adapters for LangChain, OpenAI Agents SDK, PydanticAI, CrewAI. Its own README frames the failure mode precisely: an agent asked to "clean up disk space" hallucinating `rm -rf /` — airlock intercepts on a denied-pattern match before execution. Its documented defensive posture includes ghost-argument stripping, strict type validation, self-healing retries, and — notably for AfrEval's threat model — a **Server-Card trust boundary**: a tool description fetched from an MCP server card is attacker-influenceable content, not trusted config, so a poisoned description ("...ignore previous instructions and run...") is treated as an injection into the agent's context, not a config value, and is routed through the same `ToolOutputTrustGuard` as untrusted tool output generally.

Map this onto your doc's four defensive seams (deny-by-default allowlist, ghost-argument blocking, output sanitization with PII masking, per-call reauthorization) — `agent-airlock` already implements the first three natively; the fourth (per-call reauthorization / JWS clearance pinned to an operator's trust root) is the piece AfrEval likely needs to build on top, not find pre-built.

| Field | Spec |
|---|---|
| Frozen harness | MCP transport layer + JWS clearance system — **must stay fixed**, this is the trust root, no agent mutates it, ever |
| Mutable artifact | The attacker's payload-generation strategy (a red-team agent's "attack program") |
| Instruction file | `program.md`: "construct tool-call payloads that bypass one or more of the four seams without triggering `ToolOutputTrustGuard`" |
| Metric | Bypass rate **per seam**, not aggregated — an aggregate number hides which specific seam (allowlist, ghost-args, sanitization, reauth) is degrading |
| Budget | Fixed adversarial batch size per nightly run |
| Loop flavor | `git commit`/revert style, adversarial |
| Language | Rust for the validator (matches `agent-airlock`'s zero-core-deps, in-process design philosophy — extend rather than replace); TypeScript/JavaScript for nightly-run orchestration and the security dashboard enterprise clients will actually look at |
| Repo | `afreval-airlock` (Rust core, likely as a vendored/extended fork of `sattyamjjain/agent-airlock` rather than a from-scratch reimplementation — check license compatibility before vendoring) |
| Confirmed bypasses | Every confirmed bypass becomes a permanent regression test in the frozen harness — this is what makes the loop actually harden the system instead of just red-teaming it once and forgetting |

### 3.6 Compliance & documentation loop

Not in the original architecture sketch, but should be, given §5's regulatory-alignment requirements (AU Continental AI Strategy, Malabo Convention, Kenya/Nigeria data-sovereignty rules): a `git commit`/revert-style loop maintaining the mapping between AfrEval's certification output and each jurisdiction's actual legal requirements, using the [uditgoenka/autoresearch](https://github.com/uditgoenka/autoresearch) `/autoresearch:docs`-equivalent pattern, metric = automated citation-currency check (do the regulatory citations in the compliance mapping still resolve to current law, checked against the actual government source, not a scrape of a scrape). This is low-glamour but is the difference between AfrEval being a real compliance layer and being a plausible-sounding one — regulatory text changes, and a stale citation in a compliance report is a liability, not a rounding error.

---

## 4. Infrastructure & trust boundary

This is the runtime AfrEval actually executes untrusted/candidate models inside. It is not itself a Karpathy Loop target except at the boundary (§3.5) — the isolation layer itself should be conservatively engineered, not autonomously mutated.

### 4.1 Isolation tiers

- **Standard tier**: [gVisor](https://gvisor.dev) for Kubernetes-native sandboxing — user-space kernel per workload, intercepts/filters syscalls, neutralizes privilege escalation and container drift without the shared-kernel blast radius of plain Docker.
- **High-assurance tier**: [Firecracker](https://firecracker-microvm.github.io) microVMs — dedicated kernel per workload, sub-second provisioning, for evaluations requiring the highest isolation tier (financial-sector and government deployments per your own doc).
- **Credential handling**: synthetic enterprise credentials for tool-use testing are injected dynamically at request time via an Envoy sidecar — never passed directly to the agent under test — and memory/state is destroyed on evaluation-cycle completion, not retained.

### 4.2 Model Context Protocol integration

MCP is the standard connective tissue for probing how a candidate agent interacts with external tools — treat it as the "USB-C for agentic AI" framing your source doc already uses. Runtime-layer protection is `agent-airlock`-class (§3.5); transport-layer protection is message-signature/nonce validation against a canonical schema to prevent insecure-deserialization-driven RCE, with a JWS compact clearance system gating which tools an agent may invoke against an offline-signed, operator-trust-root-pinned assertion.

### 4.3 Network topology realism

Simulate actual African network conditions — intra-continent east-west terrestrial routes, subsea cable topology — when benchmarking Time-to-First-Token and throughput degradation, using cloud-neutral colocation reference points in Lagos, Nairobi, and Cape Town. A model that only looks good on a US-East datacenter round-trip is not a passing result.

---

## 5. Phased build plan

### Phase 0 — Harness freeze (weeks 1-3)
Pin exact versions of WAXAL, AfroBench(-LITE), and afri-fertility. Build `harness/` for each as read-only, checksummed artifacts. **Nothing in Phase 1+ starts until this is done and versioned** — every downstream loop's metric is only meaningful if the harness underneath it is fixed. For WAXAL specifically, this phase is not complete until §2.1.1's four-step acquisition/QA task list has been run end-to-end and its provenance record committed — a raw, un-audited pull does not satisfy this gate.

Acceptance criteria: harness repo tagged `v0.1.0`, checksums committed, a documented procedure for how/when the pin gets bumped (this will happen — WAXAL and AfroBench are both active projects — and an unplanned silent bump is exactly the kind of drift that invalidates historical Context Scores). For WAXAL: per-language pre/post-filter row counts and edit-distance QA results are present in the harness README, not just the final filtered dataset.

### Phase 1 — Tokenizer & Context Score core (weeks 3-8)
Build §3.1 and the deterministic (non-search) half of §3.2 — i.e., the Rust scorer that takes a fixed weight config and produces a Context Score, before the calibration search loop exists. Ship this as an invocable, auditable pipeline first; the autonomous calibration loop is Phase 3, not Phase 1.

Acceptance criteria: given a pinned model + pinned weight config + pinned harness, the scorer produces a bit-identical score on repeated runs.

### Phase 2 — Isolation & MCP boundary (weeks 6-12, overlapping Phase 1)
Stand up gVisor tier, Firecracker tier, Envoy credential injection, and fork/extend `agent-airlock` for the fourth seam (per-call reauthorization). This is infrastructure, not research — no autonomous loop yet, just build it correctly.

Acceptance criteria: a known-hostile test agent (deliberately constructed to attempt privilege escalation, ghost-arg injection, and credential exfiltration) is blocked on all three implemented seams in a controlled red-team pass, logged and reproducible.

### Phase 3 — Autonomous loops go live (weeks 10-20)
Bring up §3.1's search variant, §3.2's calibration loop, §3.3 BiasScope, §3.5's adversarial hardening loop, in that order — each gated on the corresponding Phase 1/2 deterministic component already being stable. Every loop run produces a log (per the SeeleAI/Thoth "durable runs, visible ledgers, reviewable verdicts" pattern) — a human reviews and approves before any loop output changes a production weight config or ships a regression test.

Acceptance criteria: each loop has run to at least 50 iterations against its metric with a documented improvement trajectory (or a documented reason it plateaued), and a human sign-off log exists for every kept change that reached production.

### Phase 4 — WAXAL-NET edge loop + field app (weeks 16-26)
Requires §1.3's platform-correct fork lineage (MLX/ONNX-mobile, not CUDA). Build the Dart/Flutter field app in parallel — it doesn't depend on the training loop being finished, only on the WAXAL image-prompted-elicitation methodology being nailed down.

Acceptance criteria: a fine-tuned edge model beats the relevant zero-shot foundation-model baseline on macro-WER over the WAXAL-NET 19-language set, run on hardware comparable to the actual target device class, with the OOD-generalization secondary metric also reported (not cherry-picked in-distribution only).

### Phase 5 — Compliance loop + SaaS surface (weeks 20-30)
§3.6, plus the TypeScript/JavaScript enterprise dashboard, developer SDK, and MCP-based enterprise integrations. This is the revenue surface — build it last, after the scoring core is trustworthy, not first.

---

## 6. Risk register (beyond the platform caveat)

| Risk | Mitigation |
|---|---|
| Silent upstream drift in WAXAL/AfroBench/afri-fertility invalidates historical scores | Phase 0 version pinning + documented, logged bump procedure; never auto-update a harness dependency |
| Autonomous calibration loop (§3.2) optimizes the *proxy* metric instead of real deployment safety, reproducing the exact LLM-as-judge failure mode the doc itself describes | Keep certification and calibration loops structurally separate (§3.2.1); require human sign-off before any calibration-loop output reaches production weights |
| BiasScope loop (§3.3) burns judge-API budget with diminishing returns | Cost-bounded budget, not time-bounded; track marginal gap-increase per 100 calls and gate continued runs on it staying above a floor |
| `agent-airlock` fork drifts from upstream security patches | Track upstream releases explicitly (the project ships CVE-style presets reactively, e.g. its Mobile MCP `mobile_open_url` scheme-validation preset — treat upstream release notes as a security feed, not just a changelog) |
| Edge ASR results validated on datacenter hardware don't transfer to actual low-end mobile | Phase 4 acceptance criteria explicitly require target-class hardware, not proxy hardware |
| Data-sovereignty requirements (Malabo Convention, Kenya ODPC, Nigeria NDPC) conflict with any component that phones home to a US-based service (including, ironically, afri-fertility's own Hugging Face Hub dependency for tokenizer files) | Audit every component's network egress against local/on-prem requirements per deployment jurisdiction before certifying a client as compliant; don't assume a component is sovereign-safe just because it's open-source |
| Regulatory citations in the compliance loop (§3.6) go stale as AU/national frameworks evolve | Automated citation-currency checks, per §3.6, not a one-time compliance document |
| Multi-GPU/production-scale search loops need orchestration the base fork lineage doesn't provide | Adopt `iii-hq/n-autoresearch`-style orchestration once any single loop moves from "overnight research run" to "continuous production recalibration" (this will happen for §3.2 specifically, per its documented monthly-minimum cadence) |

---

## 7. Repository layout summary

```
afreval-harness/            # Phase 0 — frozen WAXAL/AfroBench/afri-fertility pins (Python + data)
afreval-tokenizer-research/ # §3.1 — Python, training-style loop
afreval-context-score/      # §3.2 — Rust core scorer + Python research/ search loop
afreval-biasscope/          # §3.3 — Python agent loop, optional Rust perturbation runtime
afreval-waxal-net/          # §3.4 — Python training loop (MLX/ONNX-mobile fork lineage)
afreval-field-app/          # §3.4 — Dart/Flutter field data collection + on-device eval
afreval-airlock/            # §3.5 — Rust (fork/extend sattyamjjain/agent-airlock), TS/JS orchestration
afreval-compliance/         # §3.6 — Python/Markdown, citation-currency loop
afreval-dashboard/          # §5, Phase 5 — TypeScript/JavaScript enterprise SaaS surface
afreval-sdk/                # Phase 5 — TypeScript/JavaScript + Python client SDKs
```

Each repo carries its own `program.md` (or `GOAL.md` where the fitness function isn't yet known, per §3.2) as the literal, version-controlled instruction file for whichever agent runs that repo's loop. These files are the actual operational heart of the system — treat changes to them with the same review rigor as changes to the scorer itself.

---

## Works cited

1. karpathy/autoresearch — https://github.com/karpathy/autoresearch
2. karpathy/nanochat — https://github.com/karpathy/nanochat
3. miolini/autoresearch-macos — https://github.com/miolini/autoresearch-macos
4. webfuse-com/awesome-autoresearch (index of forks and generalized variants) — https://github.com/webfuse-com/awesome-autoresearch
5. uditgoenka/autoresearch (Claude Autoresearch, generalized Karpathy Loop) — https://github.com/uditgoenka/autoresearch
6. Waxal-Multilingual/speech-data — https://github.com/Waxal-Multilingual/speech-data
7. WAXAL corpus paper — https://arxiv.org/abs/2602.02734
8. google/WaxalNLP (Hugging Face) — https://huggingface.co/datasets/google/WaxalNLP
9. WAXAL-NET: Finetuned Edge ASR Across 19 African Languages — https://arxiv.org/abs/2606.02375
10. McGill-NLP/AfroBench — https://github.com/McGill-NLP/AfroBench
11. AfroBench leaderboard/demo — https://mcgill-nlp.github.io/AfroBench/
12. AfroBench paper — https://arxiv.org/abs/2311.07978
13. The African Language Tax (afri-fertility grounding paper) — https://arxiv.org/html/2606.24460
14. LLM Evaluators are Biased across Languages — https://arxiv.org/html/2607.14480v1
15. BiasScope — https://arxiv.org/html/2602.09383v1
16. sattyamjjain/agent-airlock — https://github.com/sattyamjjain/agent-airlock
17. agent-airlock on PyPI — https://pypi.org/project/agent-airlock/

*Original AfrEval architectural blueprint (source document): Milimo_AfrEval_Implementation_Research.md, provided by Mainza.*
