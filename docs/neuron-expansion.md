# Neuron expansion experiment

The app now uses a **2,048-neuron motor controller**. The canonical shape planner
and wing rhythm still use the original 1,024-neuron network. The neural screen
loads the correct graph and counts for whichever network is currently displayed.

## Selection and training

Starting from the same measured 1,024-cell MaleCNS v1.0 VNC subgraph, we selected
additional intrinsic neurons by total incident synapse count with the original
cells. Selection used no shape labels. Body-ID order breaks ties. The 2,048 graph
is nested within the 4,096 graph; both retain every measured induced edge and the
original 256 sensory / 128 motor interfaces.

Every candidate warm-started from `composition-motor.pt`, with the same frozen
projection and decoder. All used seed 421, 24,000 offline actuator examples,
2,400 refinement steps and 2,048 separate checkpoint-selection examples. A
further independent physical acceptance set included the six-stroke search/feed
preset and seven unrelated four-stroke layouts, plus single-shape perturbations
and core/feedback removal.

The original bounded-gain transfer clipped some effective weights after larger
row sums changed normalization; that preliminary 2,048 transfer had command RMSE
0.1244 and was not used. Expanded comparison models instead use positive softplus
gains so original effective weights transfer exactly, with new edges initialized
at softplus(−3). The original historical models retain their bounded gains.

## Results

| Motor neurons | Measured edges | Command RMSE | Worst stroke RMSE | Mean stroke RMSE | Training seconds | Inference ms |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1,024 | 42,944 | 0.05379 | 0.015217 | 0.011376 | 20.0 | 0.118 |
| **2,048** | **192,267** | **0.05463** | **0.015292** | **0.011407** | **59.1** | **0.551** |
| 4,096 | 534,990 | 0.05498 | 0.015308 | 0.011423 | 226.6 | 1.780 |

Command RMSE is normalized actuator-command error. Stroke RMSE is in normalized
model millimetres, not actual biological millimetres. All three passed every
physical acceptance criterion: completed layouts, each stroke <0.035 RMSE and
>95% drawing contact, zero travel contacts, normal single shapes under the same
limits, perturbation recovery <0.05, and ablation error >5× normal error.

Timing is one local CPU run, not a hardware-independent benchmark. Training time
includes final validation/export calculations but excludes graph preparation,
example generation and warm-start construction. Sparse inference timings are
500 consecutive single-observation evaluations; UI and physics add overhead.
Dense training matrices alone occupy 4, 16 and 64 MiB, respectively; this is not
total process memory or peak training memory.

**More neurons did not improve this task in this comparison.** Differences in
drawing error are small; the smaller model was slightly better and faster.
We enabled 2,048 to provide the requested expansion, not because it won the
accuracy comparison. These are one-seed warm-start results, not a scaling law or
a claim that the measured topology beats random wiring.

## Are the added neurons doing anything?

On 256 independent actuator observations, all 1,024 added cells had nonzero
rates and all 149,323 added edges had nonzero gradients. Mean absolute activity
in added cells was only 0.00252. Removing just the added edges changed motor
outputs by 0.000436 RMSE. Their contribution is real but small in this warm start;
much of the useful behavior remains in the original circuit. This also explains
why many new dots look quiet. The renderer does not manufacture activity.

See `research/results/expansion-contribution.json` and
`research/audit_expansion.py`. This audit is not biological validation.

## Display and physical checks

The expanded motor has 1,769 measured soma positions; 279 cells have no position
and still contribute to inference and the mean trace. Anatomy remains the same
96 measured skeletons, remapped by body ID rather than old array indices. Wing
mode correctly returns to 1,024 cells / 42,944 connections. At most roughly 1,800
connections are sampled for the spatial display; they are not axon trajectories.

The active expansion's 4,061 sampled physical poses passed the fly-mesh clearance
check with no detected support or drawing-leg intersections. This samples the
configured trajectories and does not establish continuous collision freedom for
arbitrary motions.

The speed control changes batching only: 2/4/8 neural-control steps per display
update. Each still advances the same 20 ms control interval and MuJoCo substeps.
`research/test_speed.py` verifies identical states, contact and timing after the
same number of steps at all three settings. Every resulting frame reaches the
ink renderer. The monitor displays the last actual inference of each batch;
it does not claim to display every intermediate neural state at higher speeds.

## Reproduce

```sh
sh research/download.sh
.venv/bin/python research/expand_circuit.py
.venv/bin/python research/train_expansion.py --steps 2400
.venv/bin/python research/evaluate_expansion.py
.venv/bin/python research/audit_expansion.py
.venv/bin/python research/test_telemetry.py
.venv/bin/python research/test_speed.py
```

`active-motor.json` selects 2,048. The loader refuses a candidate whose saved
physical acceptance report does not pass. Historical checkpoints and reports
are retained for reproducibility. All compute is local; no paid API is involved.
