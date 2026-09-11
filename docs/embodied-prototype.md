# Embodied Designer Fly prototype

The informal “level 4” label means that a trained controller acts through physics and receives sensory feedback. It is not a scientific biological-fidelity classification.

## Runtime

`research/runtime.py` runs the refined shape planner, then a second independently trained measured-circuit network. The planner’s desired coordinates and the MuJoCo joint angles, velocities, physical tip error and filtered contact force form 16 engineered sensory features. The motor network outputs three bounded incremental joint-servo commands every 20 ms. MuJoCo integrates the movement at a smaller physical time step. No target-shape function or inverse kinematics runs during a live drawing step; IK supplies offline demonstrations and the initial reset pose only.

The body is tethered and the stylus is rigidly attached to a reduced three-DOF foreleg. The physical femur/tibia orientations drive the corresponding rendered meshes. The other legs and coxa have supporting visual poses. Only the stylus tip collides with paper. A positive normal contact force gates drawing; leaving contact breaks the ink segment. Renderer smoothing and geometric snapping do not alter the marks.

The contact model uses an elliptic friction cone, a 1 ms physics step, soft contact and a filtered force sensor. The pyramidal friction approximation produced tiny surface hops even under the offline expert controller. After correcting the foreleg attachment and retraining, normal contact fractions are 99.66% for the rectangle and 100% for the circle and triangle; physical coordinate RMSE is approximately 0.0142–0.0151 model mm. These are engineering validation results, not biological measurements.

The physical base is now (0.16, −0.514, 1.07) in native model coordinates, with a 45° outward cant. The femur remains 0.705 long; the lower link and attached stylus extend 1.36. This places the bend outside the compound eye, instead of passing the foreleg through the head. The controller received 6,000 additional refinement steps for this configuration; `motor-v1.pt` preserves the previous checkpoint. Geometry is still a reduced approximation, with no full-body collision or muscle model.

The viewer adds subtle procedural cuticle and eye-facet bump maps, stylized wing venation and a shallow-V resting wing pose. These visual textures are authored detail, not additional microscopy data. Departure Mono 1.500 is bundled under its SIL OFL license for the activity readout.

## Activity monitor audit

`research/test_telemetry.py` checks the actual server motor and wing payloads against independent PyTorch execution, including all neuron states, output commands and neuron-ID ordering. `tests/neural-telemetry.test.ts` verifies that repeated render frames cannot invent samples, source/task changes clear the old trace, and invalid payloads are rejected.

The monitor explicitly labels MOTOR or WING. MOTOR takes priority while drawing, even when the wing button is enabled. At rest, flapping shows the circle network used for wing motion. The spatial display shows 758 located cells and samples the graph edges for legibility. The trace is mean absolute rate over all 1,024 cells, with real sample timestamps and labeled automatic bounds. It holds without new observations and does not add artificial fluctuations. STROKE is drawing progress, not a neural activity percentage.

Each neural network retains all 42,944 directed edges in the selected 1,024-neuron MaleCNS subgraph. Edge gains, biases and leaks are trained; sensory projections, motor projections and topology are frozen. Rates reset before every four-step computation. This is supervised learning in an engineered network, with normalized mechanical parameters, not calibrated biological neurons, synapses, muscles or full-body dynamics. Neurotransmitter predictions have not yet been incorporated.

## Shape refinement and validation

Position and finite-difference derivative losses encourage straight movement; extra samples emphasize corners. Derivative loss excludes turn discontinuities. Validation records coordinate RMSE, maximum edge deviation away from turns, and exact-corner error. There is no renderer correction to these measurements.

`research/verify_models.py` validates motor commands on fresh random examples independent of training and rollout examples, and verifies NumPy sparse inference against PyTorch. Browser inference parity is checked separately for the refined planner. `research/evaluate_embodied.py` measures real physical strokes for every shape, perturbed starting angles and a joint-force pulse, frozen feedback and removed neural edges. `research/test_physics.py` checks removal of the paper, dynamical movement, coordinate consistency, and that IK cannot be called during stepping. Saved reports contain the exact thresholds and results; engineering adjustments were informed by rollouts, so these are prototype acceptance checks, not a preregistered scientific study.

## Wings

The wing button reuses the trained circle-network rhythm and maps its output to rendered wing angles. Its clock runs at a slowed viewing speed. At rest, the companion monitor shows that network’s computed activity; during drawing it shows the feedback network. There are no aerodynamic forces, muscle actuators or validated biological wing circuits. The control is accurately described as neurally driven wing animation.

## Sources

- [NeuroMechFly research](https://www.nature.com/articles/s41592-024-02497-y) and [official documentation](https://neuromechfly.org/) informed the embodiment approach. This app uses FlyGym anatomical assets and proportions with an original reduced MuJoCo model; it does not claim to reproduce the full FlyGym system.
- [MuJoCo solver parameters](https://mujoco.readthedocs.io/en/stable/modeling.html#solver-parameters) describe the soft contact constraints used here.
- [MaleCNS downloads](https://male-cns.janelia.org/download/) supply the measured connectome. A wiring dataset does not supply all physiology needed for a biological emulation.

This version runs locally with Vite and a persistent Python service. A later Vercel frontend needs a separately hosted physics backend or a browser physics port.
