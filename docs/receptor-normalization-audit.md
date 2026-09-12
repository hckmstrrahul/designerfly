# Recording normalization audit before v2 calibration

Audited 2026-09-13. No runtime changes. The reserved `hook_flexion_02_treadmill.parquet` outcomes were not opened for this audit.

## What the measurements mean

The paper's Methods describe **baseline**, not whole-trial, z-scoring: GCaMP/tdTomato ratios are centered and scaled using each trial's lowest 10% ratio values. Signals are then spline-upsampled to 300 Hz and smoothed over 0.2 s. A figure-stage maximum, shared within a genetic-driver dataset, provides the final display scale. Large positive values such as 10 or 36 therefore do not contradict z-scoring. Fully restrained magnet recordings initially use ΔF/F with a minimum 10-frame-window baseline; Extended Data Fig. 6 subsequently receives the z-score processing. Absolute transfer between preparations is consequently uncertain. The published 30/300 ms calcium-kernel constants were tuned against previous calcium measurements, not measured receptor kinetics. The paper does not specify the moving-average alignment. [Dallmann et al., Methods: image analysis and computational models](https://faculty.washington.edu/tuthill/docs/Dallmann_et_al-2025-Nature.pdf), [DOI](https://doi.org/10.1038/s41586-025-09554-2).

## What the released code actually does

Source revision: `e1233f4a987c532c9f1ab42273af21a0a6a50393`; local inventory: `work/receptor-study/tree.json`. The inventory contains analysis and plotting scripts, not a raw-image preprocessing implementation establishing the smoothing alignment.

| Author code | Observation relevant to v2 |
|---|---|
| [imaging_plot_trial.m](https://github.com/chrisjdallmann/feco-inhibition/blob/e1233f4a987c532c9f1ab42273af21a0a6a50393/code/imaging_plot_trial.m) | Divides stored `calcium` by its maximum across analyzed frames in the loaded dataset. Predictions receive their own maximum. These are display normalizers, not a shared physical unit. Optional recomputation pads each trial with 1,000 copies of its first input and subtracts the trial prediction minimum. |
| [imaging_fit_activation_function.m](https://github.com/chrisjdallmann/feco-inhibition/blob/e1233f4a987c532c9f1ab42273af21a0a6a50393/code/imaging_fit_activation_function.m) | Divides calcium by the selected analyzed ROI-frame maximum. Hook/club use a fixed-kernel predictor, then fit slope and intercept across trials with `fitlm`. This is fitted observation scaling, not training-free inference. |
| [imaging_predict_gcamp.m](https://github.com/chrisjdallmann/feco-inhibition/blob/e1233f4a987c532c9f1ab42273af21a0a6a50393/code/utils/imaging_predict_gcamp.m) | Hook flexion uses a binary velocity threshold. The kernel is `exp(-t/.30)-exp(-t/.03)`, normalized to sum one, convolved causally and truncated. No additional 0.2 s moving average is applied to predictions. For 9A, annotated passive movement is removed before thresholding absolute velocity. |
| [imaging_hook_model_example.m](https://github.com/chrisjdallmann/feco-inhibition/blob/e1233f4a987c532c9f1ab42273af21a0a6a50393/code/imaging_hook_model_example.m) | Synthetic movement demonstration; three threshold-model predictions share their combined predicted maximum. It does not identify a biological release gate or empirical observation gain. |

## Recommended preregistered v2 handling

1. Keep stored calcium units. Fit observation gain/intercept using training animals only and freeze them before validation/test. Do not divide held-out outcomes by their maximum, re-z-score them, or fit a new cohort gain after viewing results. If a training-only normalizer is used, record its exact value and apply it unchanged everywhere.
2. Fit the passive velocity-to-calcium observation model first. Preserve trial boundaries, timestamps, and excluded-frame dynamics; score only eligible frames. Use the published fixed kernel as the baseline. Additional smoothing would be a declared modeling assumption and may double-count filtering already absorbed by the fitted kernel; do not tune its alignment on the untouched cohort.
3. Fit active suppression only after freezing the passive observation model. Report both absolute prediction errors and scale-insensitive temporal measures, with animal-level uncertainty. A failure of absolute transfer can reflect preparation/driver observation differences as well as an incorrect suppression model; neither explanation licenses post-test rescaling.
4. Treat 9A calcium as a separate population observation with a separate training-only observation gain. A fitted behavioral-drive time constant is not a GABA conductance or release-gate time constant. Calcium kinetics and preprocessing blur fast effects; receptor kinetics require additional direct physiology or an explicitly non-identifiable parameter range.
5. Maintain the untouched hook02 cohort lock until code, parameters, metric definitions, and acceptance criteria are recorded. Same-cohort exploratory checks must not be relabeled independent validation.

These choices support a falsifiable calcium-level model comparison. They do not establish calibrated spike-to-release dynamics for the pencil controller.
