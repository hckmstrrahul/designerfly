# UI motor readout refinement

This update applies to NL01 **Spikes**. The original **Motor** mode is unchanged.
Draw UI primitives also supply the same explicit geometry shown in the editor,
like text and emojis; this path preparation is separate from motor training.
Every ink point remains the measured physical pencil tip, not a redrawn target.

## Method

Seed 73192 generates 32 UI stroke demonstrations (12,555 controller samples):
horizontal/vertical rules, rectangles and rounded rectangles at varied sizes and
positions. Half of the physical rollouts follow an offline IK feedback teacher;
half follow the previous motor to expose its feedback errors. The teacher labels
actuator commands only during training. Persistent LIF motor spike rates and their
temporal differences are the runtime readout inputs.

Ridge regression fits a 257-by-3 readout. The selected fit uses ridge penalty 10
and adjacent-output smoothness penalty 25 (including travel and turns). Its affine
readout is blended 15% new / 85% baseline in matching normalization coordinates.
No runtime filter, target-to-ink correction, teacher, IK or observation-to-action
bypass was introduced. The sensory projection and recurrent anatomical weights
are unchanged. No extra elbow intercept calibration was adopted.

Full replacements, stronger blends and pressure-bias variants were rejected for
contact loss or tracking regressions. Rate-teacher and broader curricula were
also explored but not selected. Lower demonstration loss alone did not establish
a better physical controller.

## Results and limits

Five small fixtures were used for model selection. The chosen conservative
readout then passed nine physical regression cases, including the complete
46-stroke newspaper, lettering, emojis and freehand. Newspaper contact improved
from 99.644% to 99.815%; its tracking RMSE changed from 0.02691 to 0.02736.
Minimum contact over individual newspaper strokes improved from 96.34% to 98.96%.
The historical learned-circle test's contact decreased to 97.61%, still above
acceptance; improvements are not universal.

A separate seven-fixture quality test was locked with seed 846219 before execution.
On equal-weight fixture averages, roughness decreased 12.64%, cross-track RMSE
12.78%, and tracking RMSE 3.87%. Contact increased 99.609% to 99.835%; all drawings
completed with zero travel contact. Roughness improved on every test fixture, but
vertical and diagonal cross-track error worsened. These are limited engineering
tests, not a biological behavior benchmark or a guarantee for all user drawings.

Roughness measures normal-direction second differences of actual contiguous
contact positions within straight segments. Cross-track distance is measured to
the intended polyline; tracking error also includes timing lag. Physics length
units are normalized model millimetres, not a calibration of a real fly.

Reports include artifact hashes:

- `research/results/ui-motor-training.json`: selected training recipe and provenance.
- `research/results/ui-motor-baseline.json`: original selection benchmark.
- `research/results/ui-motor-holdout.json`: locked fixtures and before/after results.
- `research/results/spiking-motor-validation.json`: active physical acceptance gate.
- `research/results/spiking-motor-validation-base.json`: original acceptance report.

## Reproduce without replacing the live checkpoint

The original checkpoint is retained as `research/results/spiking-motor-base.npz`.

```sh
.venv/bin/python research/train_ui_motor.py --checkpoint research/results/spiking-motor-base.npz --output-dir work/ui-reproduction --teacher ik --rollouts 32 --blend .15
.venv/bin/python research/benchmark_ui_motor.py --checkpoint work/ui-reproduction/candidate-r10-s25.npz --output work/ui-reproduction/quality.json
.venv/bin/python research/validate_spiking_motor.py --checkpoint work/ui-reproduction/candidate-r10-s25.npz --output work/ui-reproduction/physical.json
```

The training command writes candidates, never installs them. A checkpoint must
pass physical acceptance and contact-quality review before replacing the active
checkpoint and its hash-matched report. The complete locked quality-test geometry
is retained in `ui-motor-holdout.json` and can be passed to `benchmark_ui_motor.run`.

## Relation to connectome research

The Spikes controller implements persistent LIF dynamics with frozen,
synapse-count-derived recurrent weights. It uses a 2,048-neuron MaleCNS subset,
not a complete brain. Transmitter predictions supply assumed signs, without
receptor-specific validation. Engineered sensory roles, calibrated parameters,
and trained motor outputs remain necessary.

It does not replicate the biological prediction benchmark of
[Shiu et al. (2024)](https://doi.org/10.1038/s41586-024-07763-9). That paper's 91%
refers to agreement across 164 experimentally tested predictions, not general
whole-fly behavioral accuracy. Neither experiment demonstrates superiority to
human brains.
