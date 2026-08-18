# Contributing

The highest-value contribution is a **release-genealogy edge**: the typed
graph in `registry/release_graph.yaml` is what turns "same family" folklore
into decisions, and no single team can maintain it alone.

## Adding a checkpoint or edge

1. Add the checkpoint(s) under `checkpoints:` (HF id, family, release date).
2. Add the edge under `edges:` with:
   - `type`: `fresh_pretraining` | `continuation` | `anneal` | `soup`
   - `continuation_tokens`: approximate distance, for continuation edges
   - `confidence`: `verified` (provider documents the trajectory: technical
     report, model card, published intermediate checkpoints) or `inferred`
     (release notes imply it but the trajectory is not documented)
   - `note`: one line citing the source (report section, model-card quote)
3. Run `pytest tests/test_registry.py` locally.

**Evidence rules.** `verified` requires a citable provider statement or
published intermediate checkpoints. Never mark an edge `continuation`
because the architecture matches -- shape identity is exactly the signal
this project exists to debunk. If the provider is silent, the pair stays
out of the registry and users get the questionnaire.

## Other contributions

- Measured `R(Copy)` values for registry edges (link per-example records):
  these calibrate the distance budget and grow the probe dataset (RQ5).
- Task examples under `examples/` (config + comparator + README).
- Bug reports with the `recommendation.md` attached.

By contributing you agree your contribution is licensed under Apache-2.0.
