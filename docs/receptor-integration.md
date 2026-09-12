# Receptor candidate acceptance contract

The [machine-readable contract](../research/results/receptor-integration-contract.json) fixes the conditions for an experimental motor candidate. These are **engineering acceptance margins chosen before new holdout outcomes**, not published biological thresholds. Nothing here enables the gate, starts motor training, or changes the working controller.

## Fresh biological confirmation

All previously examined hook01 treadmill/platform and magnet outcomes are development data, including the former test animals. Fit preprocessing, observation kernels, scales and models within animal-grouped development cross-validation. Freeze the candidate and the strongest development-selected control from passive-derived nongated, constant and v1-style alternatives. Save model, source, code, preprocessing and contract hashes before accessing the new calcium outcomes.

The fresh primary cohort is **all eight animals in `hook_flexion_02_treadmill.parquet`**. Fresh passive transfer uses **animals 2–14 in `hook_flexion_01_magnet_Mamiya2018.parquet`**; animal 1 is excluded because its first rows were previously inspected. Confirm biological cohort provenance; numeric IDs reused in separate files do not establish identity or independence.

Score finite `analyze=1` observations under locked preprocessing. Each animal contributes equally, regardless of frame count. At least five independent eligible animals, with at least 30 scored frames each, are required per cohort; otherwise the result is inconclusive. Bootstrap paired biological animals, not frames: 20,000 replicates, fixed seed 20260913, two-sided percentile 95% intervals.

| Required result | Preregistered threshold |
|---|---|
| Primary mean MSE reduction against strongest locked control | At least 5%, with the paired 95% interval lower bound above zero |
| Primary individual benefit | At least 75% of animals improve |
| Individual protection, either cohort | No animal's MSE increases by more than 25% |
| Passive transfer noninferiority | Upper 95% bound on relative MSE increase at most 10% versus the locked nongated model |
| Passive predictive value | Passive observation head has lower held-out mean MSE than the development-fitted constant model |

Report the passive constant-comparison confidence interval, even though its lower bound is not another pass condition. If gate-off makes the passive and nongated predictions identical, say so: that noninferiority result alone provides no evidence of predictive value. Report per-animal errors, active/passive strata, correlations and amplitude errors as well as aggregate results.

Evaluate once. Do not tune on a failed holdout and then relabel it confirmation. Outcome-dependent omissions, fitted test-animal amplitude offsets and revised thresholds invalidate this contract. A materially revised candidate needs untouched confirmation data.

## A calcium fit is not yet a spike-release mechanism

The current calibration uses a normalized low-pass movement proxy in `[0,1]`. The runtime hypothesis sums discrete 9A spike events; its activation depends on event rate and time constant. **Copying fitted proxy beta/tau into that gate is invalid.** Under an assumed stationary event rate, mean event activation scales approximately as `rate × tau`; nonlinear suppression also depends on event variability, so merely rescaling beta is not sufficient evidence.

Unique biological spike-rate identification from calcium is **not** required or claimed. Instead, declare a consistent assumed spike generator, spontaneous rate, input scaling, uncertainty range and observation model. Calibrate on development observations and evaluate the complete spike-to-release-to-calcium pipeline. Preserve raw hook events separately from release-weighted transmission. Document whether time constants describe an observation kernel, movement envelope, synaptic process or receptor hypothesis.

If fresh confirmation evaluates only a movement-proxy model, its predictive result can pass while the **mechanistic bridge remains pending**. It cannot authorize motor promotion. Numerical tests must preserve event times while refining 1 ms to 0.5 ms and 0.25 ms timesteps, with no more than 1% change in release trajectories and transmitted event mass at shared evaluation times. Keep receptor blockade distinct from removal of the targeted input pathway.

## Anatomy and candidate isolation

The corrected [MANC audit](../research/results/receptor-manc-audit.json) supports 35 measured MaleCNS edges totaling 2,724 synapses; the relevant foreleg subset contains five edges and 155 synapses. Earlier zero-edge conclusions used incorrect cross-version type labels. This supports an isolated probe, not automatic inclusion in the current motor.

Lock original cell IDs, crosswalks, side/nerve/class evidence and measured edges. Document inputs and downstream outputs of newly included cells. Only approved 9A-to-hook edges move out of the ordinary somatic pathway; keep their anatomical counts and avoid double counting. Do not invent missing anatomical connections. Cross-specimen homology is not a receptor measurement for each MaleCNS edge.

Only after biological, mechanistic-bridge, anatomical and isolation gates pass may we train **candidate interfaces**. Keep internal anatomical weights and declared mechanism parameters frozen. Use separate candidate graph, checkpoint and report files listed in the JSON. Never overwrite the currently validated spiking checkpoint or active motor configuration.

Before enabling the candidate, rerun all current physical drawing acceptance tests, add unseen trajectories and targeted gate interventions, and compare tracking, contact, pen lifts, force, stability and disturbances against the unchanged baseline. A loader must verify all evidence, graph, checkpoint and runtime hashes. Keep the original controller available for rollback. An expanded candidate graph is not bitwise equivalent to the original graph merely because gating is disabled.

**Current state:** fresh confirmation, the spike-to-observation bridge, motor-compatible inclusion and candidate motor training/validation remain pending. No new locomotion capability follows from this calibration: the simulated body still has one actuated three-joint foreleg.
