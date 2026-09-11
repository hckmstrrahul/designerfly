# Local composition prototype

The app now executes manually arranged rectangles, circles and triangles at different positions and sizes on a single sheet. This extends motor execution, not prompt understanding or autonomous UI design.

## Control path

1. The editor supplies shape identity, center and bounding-box size. It allows up to eight shapes. Centers and extents stay within normalized x/y [-1, 1], corresponding to physical x [1.15, 1.95], y [-0.4, 0.4]. Box dimensions are 0.24–1.72 normalized units. This is a bounded central region of the paper; the fixed fly cannot reach everywhere on the sheet.
2. The existing trained canonical shape circuit generates the path from shape identity and phase harmonics.
3. A documented affine transform places and scales that learned path. This operation is engineering, not learned neural computation. The SVG in the editor is a specification preview; it is not used to draw the physical ink.
4. The composition motor circuit receives the intended point, joint positions and velocities, actual tip error, and filtered contact force. It outputs three joint-servo commands. The circuit retains the measured 1,024-neuron / 42,944-edge topology and frozen input/output maps.
5. MuJoCo integrates each movement. A travel/lower/draw/lift sequencer supplies timing and desired height. It never teleports/reset the body between strokes or calls inverse kinematics in live steps. Ink requires the drawing stage and actual tip–paper contact.

Circles remain round in the editor. Rectangles and triangles can change aspect ratio. Neural activity during a composition comes from the composition motor checkpoint, verified against independent PyTorch inference, including all 1,024 displayed rates. Original single-shape draws still use the previous motor checkpoint; idle wing animation still uses the canonical circle planner.

## Training and evaluation

The new motor checkpoint starts from `motor.pt`. Eight randomized four-shape training layouts provide 16,459 physical rollout observations. Offline inverse kinematics provides actuator imitation labels; half of each training batch instead uses randomized state/reference examples. 8,000 optimizer steps refine measured-edge gains, biases and leaks; input/output buffers are checked unchanged. Optimization took about 58 seconds locally, excluding data collection.

The batch diagnostic validation mixes random samples and reused rollout observations, so it is not the final independent test. `evaluate_composition.py` separately uses seed 90377 for eight held-out layouts and 2,048 fresh state/reference examples.

- All 32 held-out strokes complete with RMSE below 0.035 model mm and contact above 95%.
- Worst stroke RMSE: 0.016161 model mm.
- No paper contact during travel between shapes.
- Independent actuator-command RMSE: 0.035835 before refinement, 0.031637 afterward, 0.505471 with neural connections removed.
- Normal tracking RMSE on the intervention trial: 0.010889; removing the core: 1.593618; removing feedback: 1.315786.
- Runtime sparse inference matches PyTorch actions and rate states. Topology and fixed interfaces match the original motor network.
- Body-clearance probes detect no intersections in 3,364 sampled poses across the held-out layouts. This is a sampled geometry check, not continuous full-body collision dynamics.

Exact results: `research/results/composition-motor-training.json` and `composition-validation.json`.

## Direct placement-network experiment

An additional 20-input planner was trained for 16,000 steps to directly output positioned/scaled coordinates. Its held-out normalized coordinate RMSE fell from 0.524829 to 0.063761 but failed the predeclared 0.035 threshold. It is retained in `placement.pt` / `placement-training.json` for research and is **not loaded by the live composition runtime**. Keeping the accurate canonical neural path and an explicit placement transform produced much better physical strokes. No failed evaluation was relabeled as a success.

## Reproduce

```sh
.venv/bin/python research/train_motor.py --steps 8000 --refine --composition
.venv/bin/python research/evaluate_composition.py
.venv/bin/python research/test_composition.py
.venv/bin/python research/test_telemetry.py
node scripts/check-fly-clearance.mjs research/results/composition-poses.json
npm test
npm run lint
npm run build
```

Training resumes `composition-motor.pt` when that file exists; otherwise it starts from the original `motor.pt`. Restart the physics service after training to load new weights. No cloud compute or model API was used. Public hosting is a separate deployment task.
