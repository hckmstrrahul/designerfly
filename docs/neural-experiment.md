# Trained drawing experiment — 11 September 2026

This file records the original coordinate-only baseline. The current app adds derivative/corner refinement and an embodied MuJoCo feedback controller; see [the current prototype](embodied-prototype.md) and the root README. Baseline results below are retained for comparison.

## Circuit and computation

`research/prepare.py` verifies the MaleCNS v1.0 annotation and connection source hashes. It selects traced `vnc_*` cells, chooses 128 motor neurons by total incoming synapse count, 640 other non-sensory cells by their measured output to those motors, and 256 sensory cells by their output to those 640. Selection is independent of shape labels. It retains every edge among the resulting 1,024 IDs: 42,944 directed connections. The exact IDs, selection rule, source hashes and subgraph hash are exported. The selected edges represent aggregate measured connections, not 42,944 individual synapses.

Each decision receives a three-way task indicator, six sine/cosine clock harmonics, and a constant. A frozen random matrix injects these features only into selected sensory cells. Four leaky tanh recurrent steps propagate state through the selected graph. A frozen random projection reads two coordinates only from selected motor cells. No coordinates or next-waypoint targets are provided at inference.

The initial edge base is its synapse count divided by total selected incoming synapse count. The effective weight is `base * (0.05 + 3.95 * sigmoid(gain))`. Leaks are `0.05 + 0.9 * sigmoid(leak_parameter)`. The optimized parameters are 42,944 gains, 1,024 biases, and 1,024 leaks. Adjacency, base weights and interface matrices are immutable. Every exported coordinate uses this same core and decoder in a JavaScript sparse evaluator.

All edges are positive in this engineered model; transmitter-specific excitation/inhibition is not implemented. Signed rate state is a numerical feature, not an absolute biological firing rate. This experiment tests whether a network constrained to these measured connections can learn the three drawing functions. It does not test biological fidelity, the superiority of connectome topology, or biological learning.

## Training and validation

Teacher shapes exist only in the offline Python trainer. Adam uses batches of 128 for 1,600 updates. There are 240 training phases per shape and 241 different validation phases per shape. Three independent seeds (123, 456, 789) all passed the predeclared threshold: overall RMSE below 0.07 and below one fifth of the untrained error. Complete loss history, runtime, device, gradient audit, before/after and edge-ablation errors are saved in `research/results/training-SEED.json`.

The first run finished in 20.75 seconds on CPU. The browser exports seed 123, with RMSE reduced from 0.76465 to 0.02239; removing all recurrent connections increases it to 0.87038. The second and third runs corroborate this narrow result. No shuffled-graph baseline or novel-shape evaluation was performed, and no topology advantage is claimed.

`tests/circuit.test.ts` compares independent browser inference with the trainer's fixture, including all neuron states, to tolerance 0.00002. It also verifies that edge removal eliminates task/clock influence in the motor output and that all three saved reports pass their checks. Analytic target shapes are absent from runtime inference.

## Rendering boundary

The worker computes fresh pen coordinates at about 30 Hz. The scene applies an affine coordinate mapping onto a physical-size sheet and smooths movement over a few frames. Ink is deposited at the visible pencil tip, so small learned errors remain visible. Phase progression pauses in a hidden tab. The approach, lifting, grasp, supporting stance, inverse kinematics, and body appearance are engineered presentation, not learned muscle or contact control. The four recurrent states reset to zero between phase decisions; this is not a continuously embodied agent.

The NL–01 device projects measured soma locations for 758 selected cells with available positions. The other 266 cells participate in computation but are omitted from the anatomical scatterplot. Only measured connections between located cells are eligible for the display; a deterministic subset is shown to keep the plot legible. Colors use the magnitude of computed state, and the trace uses its mean absolute activity. HOLD retains the last computed state. This is a ventral nerve cord motor subcircuit, not a full brain rendering.

## Anatomy and sources

The 3D fly uses pinned Apache-2.0 FlyGym/NeuroMechFly meshes, mirrored where necessary, with adapted cuticle materials, bristles, articulated legs and a fine stylus. This anatomical rendering is independent of the selected circuit and has no one-to-one muscle/neuron mapping. Source links, file hashes and licenses are retained in `public/models/fly/` and the model's graph manifest.

For the external demonstration review, see `reference-review.md`. The Supabase video inspected there explicitly labels itself ANIMATED CONCEPT; it is not evidence of learned database deployment. This project's trained pen-coordinate generator is an actual local experiment, with the narrower scope specified above.
