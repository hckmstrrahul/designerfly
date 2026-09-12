# Tonic-release v3 — bounded development protocol

Written before fitting. This is one final development-only revision of failed v2. No hook02 or Mamiya2018 final-cohort data may be read. The previous v2 report remains unchanged.

The hypothesis is that placing every calcium baseline outside a suppression gate omits an optional suppressible tonic component. This is a modeling assumption, **not evidence that hook afferents have a particular tonic firing rate**, and the simulator's engineered tonic drive is not biological evidence.

For each existing development outer fold, retain exactly the v2 passive-selected velocity response/calcium kernel and measured-9A-calcium-selected behavioral-drive time constant. Do not change those grids or selections. Let `release = 1 / (1 + beta × lowpass(L1_move))`. Predict:

`calcium = a × observe(response(velocity) × release) + b × observe(release) + offset`

Fit a,b ≥ 0 and an unrestricted offset on active training animals, with equal total animal weight. Passive recordings cannot separately identify tonic amplitude and offset, so b is fit only on active development data. The gate input remains observed behavior, not measured 9A spikes. The observation filter and resets remain exactly as in v2.

Choose beta only from .5, 2 and 8 using inner leave-one-animal-out cross-validation. Use the same three outer animal folds (seed 20260913). The mandatory new movement-only control sets a=0 and independently selects beta from the same grid, with its own training-only b and offset. Also compare the unchanged v2 candidate, v1-style, nongated and constant controls using their previously frozen predictions on these same outer folds.

The strongest control is chosen by aggregate outer-fold equal-animal MSE, never by reserved-cohort outcomes. Report per-animal errors, correlation and behavior strata; paired whole-animal bootstrap uncertainty; coefficient/grid-boundary stability; and comparison specifically against movement-only. Development improvement must be meaningful against the strongest control before considering a final reserved evaluation. If the apparent benefit is explained by movement-only prediction, say so and do not call it sensory or receptor validation.

The regression uses sufficient statistics and nonnegative least squares with a free intercept. The intercept is eliminated by training-only weighted centering; all feasible active sets of the two nonnegative coefficients are evaluated. No validation/test-dependent calcium normalization or intercept fit is allowed. The source tables' original preprocessing remains unchanged, with its documented limits.

Artifacts record v2 report, protocol, source and code hashes. There are no runtime, checkpoint or simulation changes.
