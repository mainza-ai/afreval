---
type: synthesis
tags: [synthesis, open-questions, discrepancies]
updated: 2026-07-31
---

# Synthesis & Open Questions

The evolving cross-source synthesis. This page is the accumulated judgment of everything ingested so far — the confirmed thesis, the still-open questions, and the places where the two source documents disagree. Updated on every ingest and lint.

## The confirmed thesis

Global frontier models structurally fail in African digital ecosystems for three measurable reasons, and all three are *implementation-recoverable* — not intrinsic:

1. **Tokenization**: BPE/unigram vocabularies learned on high-resource corpora fragment African words, imposing a 1.7×–3.3× mean fertility premium (up to ~9× on N'Ko) before a single forward pass. ([african-language-tax](concepts/african-language-tax.md))
2. **Evaluation**: LLM-as-judge systems are uncertainty-driven and systematically over-generous to low-resource languages; pairwise accuracy is structurally blind to the resulting absolute-score drift. ([llm-as-judge-bias](concepts/llm-as-judge-bias.md))
3. **Execution**: agents that can call tools must be evaluated in genuinely hardened, air-gapped sandboxes — the sandbox itself is a target.

The unifying build insight: **every subsystem of AfrEval can be a Karpathy Loop** ([karpathy-loop](concepts/karpathy-loop.md)), not just the ML training. The original `autoresearch` repo is a training-loop pattern; the generalization of the loop (git commit → verify → keep/revert) covers the four non-training subsystems.

## Cross-source consistency check (as of 2026-07-31)

Both documents agree on: the Context Score's three vectors; WAXAL's ~1,250h ASR scale and image-prompted elicitation methodology; the WAXAL-NET finding (38.0% vs 64.9% macro-WER for fine-tuned edge vs zero-shot foundation models); AfroBench's 64 languages / 15 tasks / 22 datasets; the African Language Tax framing; and the four-seam defensive architecture with agent-airlock.

## Flagged discrepancies & open parameters

| Item | Bible (§) | Research | afri-fertility repo | Action needed |
|---|---|---|---|---|
| WAXAL language count | "21–27 languages depending on release" (§2.1) | "24 Sub-Saharan African languages" | Hub publishes **19 `_asr` configs** (verified 2026-07-31) — matching the WAXAL-NET set; `_tts` configs add more (hau, ibo, swa, yor, …). Pin the 19 ASR configs; the 21–27 figure spans ASR+TTS across releases |
| WAXAL TTS hours | "~180–235 hours, varies by revision" (§2.1) | "over 235 hours" | — | Pin exact paper revision |
| afri-fertility corpus size | "pinned 20-language/3-script table" (§3.1) | "20 languages, five language families, three scripts" (table) | 23 languages / 5 tiers in README; 22 in `languages.yaml` | Reconcile: is the harness corpus 20, 22, or 23? |
| Code-mixing metrics | "weighted toward code-switching robustness" (§3.2) — no formulas | Full CMI / I-index / M-index formulations (§"Mathematical Quantification of Code-Mixing") | — | **Gap:** the Bible's Linguistic Fidelity spec does not formalize the Research doc's code-mixing math. Decide whether CMI forms part of the harness or is deferred. |
| Context Score threshold | "below the mandated regulatory or corporate threshold… blocks deployment" — no number | same, no number | — | The 0–100 scale and per-vertical thresholds are unspecified — first deliverable of the [calibration loop](subsystems/context-score-calibration.md) |

## Open questions worth investigating

- **What is the minimum Context Score?** The docs say deployment is blocked below a threshold but never define it. Needs a first cut for Phase 1 and calibration against incident-labeled history for Phase 3.
- **Is the WAXAL corpus 19, 21–27, or 24 languages?** The WAXAL-NET benchmark (§3.4) uses 19; the WAXAL dataset spans more. These are different artifacts — the harness must pin each separately.
- **Do the Research doc's code-mixing indices (CMI, I-index, M-index) need a dedicated eval harness?** No script/formula appears in the Bible's substrate list. Likely a Phase 1+ decision.
- **Tokenizer-loop script stratification**: the metric is "script-stratified, three numbers, not one" (§3.1). Which 20 languages / 3 scripts exactly? Cross-check against afri-fertility's tiers (Latin breadth + Non-Latin + core).
- **WAXAL-NET hardware-class assertion** (§3.4, device layer task #4): what is the exact "target hardware class" for Phase 4 acceptance? Must be defined before the search loop can size its budget.
- **Which deployment jurisdiction is the compliance loop anchored to first?** Kenya, Nigeria, or AU-level? (§3.6, §5 Phase 5.)

## Suggested sources to look for next

1. WAXAL paper (arXiv 2602.02734) revision diff — resolve the language/hour discrepancies.
2. WAXAL-NET paper (arXiv 2606.02375) full text — exact 19-language list and eval protocol.
3. "The African Language Tax" PDF already in `dev-docs/` (`2606.24460v1.pdf`) — verify the §3.1 corpus scope.
4. agent-airlock upstream releases (security feed, per §3.5) — the Mobile MCP `mobile_open_url` preset pattern.
5. AU Continental AI Strategy implementation progress — to anchor §3.6 citation-currency checks.
