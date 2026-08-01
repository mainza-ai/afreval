# research — Context Score calibration search loop (Phase 3)

Placeholder for the §3.2 calibration loop. **Do not build the search loop yet.**

Per the GOAL.md pattern (§3.2): the fitness function is not yet known. Two passes, in order:

1. **First loop pass** — construct the labeled-outcome dataset: models that passed
   certification and later caused incidents vs. models that held up in production.
   Until this dataset exists, there is nothing to optimize against.
2. **Second loop pass** — search `weights/{vertical}.yaml` against that dataset,
   calling the Rust scorer (`afreval-context-score`) over FFI or gRPC.

Until then, the deterministic scorer in `../` is the deliverable. Human sign-off is
required before any calibration output reaches production weights (§3.2.1).
