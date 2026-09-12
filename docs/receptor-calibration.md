# Hook calcium suppression calibration

This experiment fits a small **phenomenological model of recorded calcium**, not receptor kinetics, a synaptic conductance, biological 9A firing, or a motor controller. It makes no runtime changes.

## Data and locked split

The source is Dallmann et al. (2025), Dryad [10.5061/dryad.gqnk98t16](https://doi.org/10.5061/dryad.gqnk98t16). The main recording is `hook_flexion_01_treadmill_platform.parquet`. The source README describes calcium as an already normalized/z-scored GCaMP/tdTomato fluorescence ratio and joint velocity in degrees per second. This analysis does not perform additional normalization using validation/test calcium. The authors' upstream fluorescence processing cannot be undone from this table.

Animal assignments are loaded from the independently locked `research/results/receptor-recording-split.json`, with input checksums verified before fitting. Identical numerical IDs across files are conservatively treated as the same animal, although cross-experiment identity is not established. In the main recording there are eight training animals, three validation animals and only two test animals (3 and 13). No trial or ROI from one animal crosses those partitions.

## Model and fitting

A hook activation is `velocity < threshold`. Observed behavioral `L1_move` is filtered by a causal first-order filter with time constant `tau`. Activation is multiplied by `1 / (1 + beta * filtered_movement)`. This is **observed movement gating, not a measured 9A input** and not a causal intervention model.

The gated activation passes through a calcium observation kernel with fixed 0.03 s rise and 0.30 s decay constants. The implementation cascades two unit-gain first-order filters, the continuous-time equivalent of a normalized difference-of-exponentials impulse kernel. The discrete cascade has approximately one native sampling interval of onset difference from directly sampling that analytic kernel. These constants are fixed assumptions in this calibration, not quantities estimated from the recordings.

All native approximately 300 Hz timestamps are processed. Each continuous animal/trial/ROI segment uses its measured median timestep; sampling variability exceeding 1% raises an error. State resets at trial/ROI boundaries, nonfinite dynamic inputs, nonincreasing time, or gaps greater than `max(0.02 s, 3 × median dt)`. Excluded `analyze=0` frames still update dynamics. Every third native sample is eligible for scoring, and only finite calcium with `analyze=1` is scored. Thus scoring is approximately 100 Hz without downsampling the dynamics.

A nonnegative amplitude and unrestricted offset are fitted on training animals only, weighting each animal equally regardless of recording duration. Thresholds −5, −20, −50, −100 and −200 degrees/s, gate times 0.03, 0.10, 0.30 and 1 s, and beta values 0.5, 1, 2, 5 and 10 are evaluated on validation animals only. The nongated beta=0 baseline separately selects its threshold on validation data. A constant predictor uses the equally weighted training-animal mean. Neither amplitude nor offset is refitted on validation, test, or external data.

The selected models are evaluated once on held-out test outcomes. Overall MSE/RMSE are equally weighted across animals. The report also contains per-animal errors, Pearson correlation and R² against the corresponding animal's mean. The latter is only an evaluation diagnostic, not a model normalization or fitted test-time intercept. Behavior strata are `active` and `not_actively_moving`; absence of active movement is not evidence of externally imposed passive movement. Strata with fewer than 30 scored samples per animal are not aggregated.

Paired uncertainty resamples whole test animals, not frames, 10,000 times with a fixed seed. With just two main test animals, this interval is descriptive and provides weak evidence about a population. Frames and trials are not independent replication units.

## Secondary passive transfer

The selected models, including their training amplitude/offset, are applied without further tuning to test animals in `hook_flexion_01_magnet.parquet`. This fully restrained experiment has externally imposed movement, so behavioral movement drive is set to zero. The remaining globally held-out animal is 11. This is a small, different-acquisition transfer check; failure could reflect input/normalization-domain differences as well as model inadequacy. It is not used to select or refit the primary model.

## Limits

- No supplied `predicted_calcium` column is read or fitted.
- Behavioral movement is correlated with many potential causes. Suppression inferred from this proxy cannot establish a 9A→hook mechanism or receptor-specific signaling.
- Calcium is a slow, processed readout, not a direct synaptic current or firing-rate measurement.
- The fitted beta has units tied to a normalized binary movement proxy. It is **not interchangeable** with a runtime gate driven by weighted spike impulses; neither beta nor tau should be silently transferred into that model.
- Fixed rise/decay times, binary velocity activation, global amplitude/offset and a restricted grid can miss important dynamics. A grid-boundary optimum is not a precisely identified parameter.
- Predictive failure is reported as failure; passing this comparison would still not validate receptor kinetics or improve the pencil controller by itself.

## Reproduce

```sh
.venv/bin/python research/calibrate_receptor_recordings.py \
  --data-dir /path/to/doi_10_5061_dryad_gqnk98t16__v20250903
.venv/bin/python -m unittest discover -s research -p test_receptor_recording_calibration.py
```

The machine-readable output is `research/results/receptor-calibration.json`. It records source and split SHA-256 hashes, all validation candidates, selected parameters, per-animal outcomes and the uncertainty calculation.

## Recorded outcome

**No production promotion. Receptor calibration remains incomplete.** On the locked two-animal main test, the movement-gated candidate reduced equal-animal MSE from 77.151 to 67.923 (**11.96%**) and RMSE from 8.784 to 8.242 (**6.17%**), in the source calcium units. The nongated fit collapsed to amplitude zero, so it is simply the training-mean constant; its selected velocity threshold has no identified significance.

The candidate chose a −50 degrees/s activation threshold, 0.03 s gate time constant and beta 10, with amplitude 31.448 and offset 10.251. Both gate time and beta sit at grid boundaries. They are not precise mechanistic estimates.

One main test animal improved (13: RMSE 9.131 → 7.932, correlation 0.637), while the other worsened (3: 8.422 → 8.540, correlation 0.041). The animal-bootstrap 95% interval for baseline-minus-gated MSE is **[−1.995, 20.451]**, crossing zero. With only two animals this interval is especially weak evidence. It is not appropriate to call the result validated biological suppression.

The fully restrained external animal worsened in absolute prediction error: RMSE **8.618 → 9.556**, despite gated correlation 0.649. This illustrates why correlation alone is insufficient and why the global amplitude/offset transfer is inadequate. The result is a useful fitted phenomenological candidate and an explicit failed transfer check, not completed receptor-level calibration. No hyperparameters were adjusted in response to test outcomes.
