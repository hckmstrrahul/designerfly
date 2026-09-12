# Receptor refinement: integration deferred

The requested refinement experiments have run. Neither new development model
outperformed the strongest calcium-prediction control, so no receptor mechanism
was integrated into the pencil controller and no new motor training was started.
This is a scientific model-selection failure, not an unavailable-data blocker.

## What changed

- Audited the study's baseline z-scoring and preparation-specific fluorescence
  measurements. Large stored calcium values are expected; test animals are not
  rescaled using their outcomes.
- Calibrated passive sensory response separately from movement-related
  suppression, with 9A calcium constraining a behavioral-drive timescale.
- Evaluated three outer animal folds, with inner animal-level parameter
  selection. All old hook01 test animals are now explicitly development data.
- Tested an additional suppressible tonic component with nonnegative phasic and
  tonic gains. Included a movement-only control to distinguish sensory value
  from behavior recognition.
- Locked stronger controls, source hashes, quality criteria and separate future
  confirmation cohorts. The 8-animal hook02 cohort and 13 reserved Mamiya animals
  have no outcomes read by these experiments. The published observation-kernel prior
  historically used Mamiya measurements, so that transfer set is not independent
  of every piece of prior model knowledge.

## Development results

Equal-animal calcium MSE; lower is better. These are **development cross-validation**
results, not new confirmatory tests or physical drawing errors.

| Model | MSE |
|---|---:|
| Strongest active-only control | 50.13 |
| Passive-first suppression candidate | 63.03 |
| Passive-first with suppressible tonic component | 61.91 |
| Movement-only release control | 66.31 |

The tonic revision improves on the passive-first candidate and on movement-only
prediction, but is still 23.5% worse than the strongest control. Only 1 of 13
animals improves relative to that control. The passive and 9A submodels each
beat their constant controls; that does not make their combined model adequate.
The earlier 12% advantage over a weaker nongated comparator was insufficient
evidence for integration.

The rejected models assume that passive-derived sensory dynamics transfer to
active preparations with a fitted observation gain/offset. These results suggest
that assumption is inadequate in the tested model family. They do not establish
whether physiology, fluorescence processing, unobserved behavioral state or
another source is responsible. Longer fitting or adding neurons is not a
validated remedy.

## What remains before integration

A revised sensory/observation model must demonstrate generalization against the
strong controls, followed by a consistent spike-event-to-release-to-calcium
bridge. The present fitted parameters operate on a normalized movement proxy,
not measured 9A spike events, and cannot be copied into the runtime gate.

Only then should the relevant measured foreleg cells be added to a separate
candidate graph, its motor interface trained, and drawing accuracy, paper
contact, pen lifts, force, stability and perturbation responses validated. The
current 2,048-neuron graph, checkpoint and runtime hashes still match the
validated baseline. Unused confirmation cohorts are preserved instead of being
spent on an already unsuccessful development candidate.

See [v2 methods](receptor-calibration-v2.md), [v3 methods](receptor-calibration-v3.md),
[normalization audit](receptor-normalization-audit.md), and
[integration requirements](receptor-integration.md). The machine-readable status
is `research/results/receptor-refinement-decision.json`.
