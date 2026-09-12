# Tonic-release v3: development result

**The bounded tonic-release revision also failed to beat the strongest control.** No reserved hook02 or Mamiya2018 outcomes were read, and no runtime changes are justified.

| Outer-fold development model | Equal-animal MSE |
|---|---:|
| Tonic + phasic suppression candidate | 61.91 |
| Movement-only control | 66.31 |
| Previous passive-first v2 | 63.03 |
| Nongated sensory control | 67.25 |
| Training-mean constant | 67.11 |
| Active-only v1-style control | **50.13** |

The tonic candidate reduced error relative to v2 by about 1.8%, and relative to movement-only by about 6.6%. The paired animal-bootstrap interval for movement-only-minus-candidate MSE was [0.34, 9.03]. Therefore the additional phasic feature contributes some development predictive information beyond observed movement alone.

However, error remained **23.5% worse than the strongest v1-style control**. The paired control-minus-candidate interval was [−20.76, −4.40], and only one of thirteen animals improved. This does not meet the requirement for meaningful superiority to the strongest fair control. The reserved cohorts should remain untouched rather than becoming another tuning opportunity.

The full-development fitted coefficients were phasic amplitude 29.469, tonic amplitude 2.770 and offset 9.452, with beta 8 and the same passive/9A-derived configuration as v2. These coefficients describe processed calcium under an assumed behavioral gating model. The nonzero tonic coefficient is not proof of biological spontaneous hook activity, an inferred spike rate, or an identified receptor mechanism.

Protocol: `receptor-calibration-v3.md`. Results: `research/results/receptor-calibration-v3-development.json`. The three regression tests cover equivalence to centered NNLS, equal-animal weighting/held-out exclusion, and the movement-only feature restriction. All previous v2 results remain unchanged.
