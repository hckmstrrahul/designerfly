# Passive-first calibration v2: development result

**The preregistered passive-first candidate did not beat the strongest control. No runtime integration is justified.** The reserved hook02 and Mamiya2018 cohorts were not loaded or evaluated.

The experiment followed `receptor-calibration-v2.md`. The development-only results are in `research/results/receptor-calibration-v2-development.json`, with a separate preregistration artifact containing source hashes, protocol/code hashes, grids and deterministic outer animal folds. All previously examined hook01 animals were development data; none of these scores is a fresh-test result.

| Development prediction | Equal-animal MSE |
|---|---:|
| Passive-first gated candidate, active hook01 | 63.03 |
| Passive-derived nongated control | 67.25 |
| Active training-mean constant | 67.11 |
| Active-only v1-style control | **50.13** |
| Passive sensory candidate | 36.39 |
| Fixed-kernel passive baseline | 36.78 |
| Passive training-mean constant | 69.00 |
| Behavioral drive → measured 9A calcium | 56.70 |
| 9A training-mean constant | 130.98 |

The candidate's active error was approximately 25.7% worse than the v1-style control. Only one of thirteen active animals improved. The paired animal-bootstrap interval for control-minus-candidate MSE was **[−22.23, −5.35]**. This is development evidence against the proposed forced transfer of passive-selected velocity/calcium dynamics to active recordings; it is not a reason to weaken the acceptance criteria.

The passive sensory model and behavioral-drive calcium model each carry predictive information relative to their own constants. Combining them does not automatically produce a better suppression model. In particular, observed movement timing that predicts 9A calcium does not identify its spikes, receptor kinetics, or the effective input scale of a runtime event-driven gate.

The full-development frozen candidate uses binary flexion below −100 degrees/s, calcium rise/decay .03/.15 s, movement-drive time .03 s and beta 8. The active observation head is amplitude 28.390 and offset 11.148. These remain phenomenological parameters at grid boundaries. The control selected using development outcomes is the active-only v1-style model, not the easier nongated baseline.

The final datasets remain available for a future genuinely frozen candidate, subject to the acceptance protocol. They must not be consumed as additional tuning data. No production controller, drawing checkpoint, or spiking receptor gate was changed.
