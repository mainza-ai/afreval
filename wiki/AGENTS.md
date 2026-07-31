---
type: schema
updated: 2026-07-31
---

# Wiki Schema & Operating Conventions

This file is the schema layer of the Milimo AfrEval wiki. It tells any LLM agent how the wiki is structured, how to write pages, and what workflows to run for **ingest**, **query**, and **lint**. It is co-evolved with the human owner — when a convention stops working, edit this file and update the affected pages.

## The three layers

1. **Raw sources** — `dev-docs/` (immutable, never edited by agents): `Milimo_AfrEval_Implementation_Bible.md`, `Milimo AfrEval Implementation Research.md`, and the paper PDF `2606.24460v1.pdf`. The three substrate repos (`autoresearch/`, `AfroBench/`, `afri-fertility/`) are **vendored in-repo** (flattened for re-engineering; `AfroBench/lm-evaluation-harness/` is a git submodule of EleutherAI/lm-evaluation-harness) and are also read-only source material.
2. **The wiki** — `wiki/`, this directory. Owned entirely by the LLM. Every page here is generated and maintained by the agent; the human only edits `AGENTS.md` conventions with the agent.
3. **The schema** — this file.

## Directory structure

```
wiki/
├── AGENTS.md                  # this schema
├── index.md                   # content catalog — READ FIRST on any query
├── log.md                     # chronological, append-only activity record
├── home.md                    # overview / landing
├── synthesis.md               # evolving cross-source synthesis + open questions
├── concepts/                  # durable ideas: patterns, phenomena, metrics
├── substrates/                # the frozen eval data sources
├── subsystems/                # the six Karpathy-loop subsystems (§3)
├── infrastructure/            # runtime / trust boundary (§4)
├── strategy/                  # regulatory + business layer
├── build-plan/                # phases, risks, repo layout (§5-7)
└── sources/                   # one page per ingested source doc
```

## Page conventions

- **Frontmatter**: every page starts with YAML frontmatter: `type` (`concept` | `substrate` | `subsystem` | `infrastructure` | `strategy` | `build-plan` | `source` | `synthesis` | `schema` | `overview`), `tags`, and `updated: YYYY-MM-DD`.
- **Links**: use relative markdown links (e.g. `([Context Score](concepts/context-score.md))` from the wiki root, or `../concepts/…` from a subdirectory page). A page that mentions another wiki concept must link to it at least once. No orphan concepts: every page should have at least one inbound link from `index.md`, `home.md`, or a related page.
- **Source citations**: when a claim comes from a source doc, tag it `[Bible §3.1]` or `[Research]` so provenance is traceable. Don't inline the whole source; link to `sources/implementation-bible.md` / `sources/implementation-research.md`.
- **Contradictions**: when sources disagree (e.g. language counts, hour figures), do NOT silently pick one. Record both, flag the discrepancy, and note it in `synthesis.md` under "flagged discrepancies".
- **Numbers**: preserve exact figures (percentages, multiples, hours, headcounts) — they are the analytical payload.
- **No duplication**: pages are the single home of their topic. Cross-link rather than copy content.

## Workflows

### Ingest
When a new source is dropped into `dev-docs/` and the human says "ingest":
1. Read the source fully.
2. Write its source page in `sources/` (type `source`) — what it is, what it adds, what it changes.
3. Update every affected page across the wiki (concepts, substrates, subsystems, etc.), per the contradiction rule above.
4. Update `index.md` (new entries + changed one-liners).
5. Append an entry to `log.md` with the exact prefix format: `## [YYYY-MM-DD] ingest | <Source Title>`.
6. Report to the human: what was added, what changed, what's now contradicted.

### Query
1. Read `index.md` first; select relevant pages.
2. Read those pages; synthesize an answer with citations to wiki pages (and through them, to sources).
3. If the answer is durable knowledge (a comparison, analysis, decision), offer to file it back into the wiki as a new page.

### Lint
Periodically, health-check the wiki:
- Contradictions between pages; stale claims superseded by newer sources.
- Orphan pages (no inbound links) and missing inbound links on hubs.
- Important concepts mentioned but lacking their own page.
- Missing cross-references and data gaps.
- Propose new questions to investigate and new sources to look for.
- Append a `## [YYYY-MM-DD] lint | <summary>` entry to `log.md`.

## Ground rules

- Never edit `dev-docs/` or the substrate repos.
- `log.md` is append-only — never rewrite past entries.
- Keep `index.md` in sync with every add/change; it is the agent's navigation layer.
- The human reviews all wiki edits; when in doubt about emphasis, ask.
