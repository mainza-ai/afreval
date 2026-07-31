---
type: source
tags: [source, implementation-bible, build-spec]
updated: 2026-07-31
---

# Source: Milimo AfrEval Implementation Bible

**Path:** `dev-docs/Milimo_AfrEval_Implementation_Bible.md` (immutable raw source — never edited)
**Version:** 1.0 — "Source-of-truth build spec for AI-agent-driven implementation"

## What this document is

The operating spec for building Milimo AfrEval end to end, written to be read and **executed by an AI coding agent** (Claude Code, Codex, or equivalent), not just a human. Every subsystem follows the same rule: **state the frozen harness, the mutable artifact, the instruction file, the metric, and the budget before writing a line of implementation code.**

## Structure (five parts)

1. **Core design pattern** — the [Karpathy Loop](../concepts/karpathy-loop.md), including the multi-platform caveat and its resolution (re-engineer, don't fork).
2. **Data & benchmarking substrate** — [WAXAL](../substrates/waxal.md), [AfroBench](../substrates/afrobench.md), [afri-fertility](../substrates/afri-fertility.md) as frozen harnesses; includes the agent-executable WAXAL acquisition & QA task list (§2.1.1).
3. **System architecture** — six subsystems ([§3.1](../subsystems/tokenizer-search.md) through [§3.6](../subsystems/compliance-loop.md)), each mapped to a loop, a language, and a repo.
4. **Infrastructure & trust boundary** — [isolation tiers](../infrastructure/isolation-tiers.md), [MCP](../infrastructure/mcp-execution-boundary.md), and how the loop hardens the boundary over time.
5. **Phased build plan** — [repo layout](../build-plan/repository-layout.md), milestones, acceptance criteria, [risk register](../build-plan/risk-register.md).

## Key facts

- Author's framing: AfrEval is built on the generalized Karpathy Loop — "not every subsystem is an ML training loop, but every subsystem can be a Karpathy Loop."
- Zero runtime/code dependency on any third-party autoresearch fork; the forks are technique references only.
- §3.5 agent-airlock is the **one deliberate exception** to re-engineer-don't-depend — build on it as a vendored dependency.
- Certification and calibration loops must stay structurally separate (§3.2.1).

## Related

- [Source: Implementation Research](implementation-research.md) — the earlier blueprint this operationalizes
- [Synthesis](../synthesis.md) — discrepancies between the two docs
