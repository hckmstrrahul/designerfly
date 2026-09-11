# Current Designer Fly capabilities

The precise description is **a trained, connectome-constrained rate-network controller acting through a simplified physical foreleg**. It is real neural computation and real learned parameter optimization. No LLM chooses the pen path and no analytic shape is used as the live drawing path.

## Demonstrated

| Capability | What the evidence supports |
| --- | --- |
| Three drawing paths | A learned planner generates rectangle, circle and triangle coordinates from the chosen shape and a clock. Validation covers unseen phases within those same families. |
| Positioned, resized compositions | An editor specifies up to eight shapes within the bounded reachable area. Explicit placement/scale transforms feed the neural motor controller. The active expanded controller passes eight independent layouts / 34 strokes, including an editable search/feed preset. The fly does not choose the layout. |
| Simulation speed | 1× / 2× / 4× batches more complete neural/physics steps; tests require identical trajectories and contact samples. It does not learn faster physical-time movement. |
| Pen lifts between shapes | An engineered stage sequencer commands lift, travel, lower and draw through the neural motor policy in one continuous physics session. All held-out travel intervals have zero paper contact. |
| Foreleg actuation | A second trained network commands three joint servos. MuJoCo determines the actual resulting poses and tip contact. |
| Sensory correction | Joint positions, velocities, tip error and filtered contact force enter the policy. Frozen-feedback trials fail while normal trials draw. |
| Limited disturbance recovery | Tested starting-angle offsets and a brief force pulse are corrected in the validated scene. This does not imply recovery from arbitrary disturbances. |
| Physical ink gating | Marks appear only while the simulated tip contacts the paper. Removing the paper removes all contact marks. |
| Wing rhythm | The circle network’s output supplies a rhythm for visual wing joints. This is an engineered reuse of that signal, not a learned flight behavior. |
| Neural activity display | Actual network states, indexed against the measured graph, are displayed. Enabling flapping selects the wing network; Drawing / Wings selects either controller while both run. |

## Not demonstrated

Prompt understanding, autonomous UI design, new shape families, sizes/locations outside the bounded trained workspace, seeing the canvas through eyes, handwriting, online learning from new drawings, full-body walking, free pencil grasping, aerodynamic flight, biological plasticity, consciousness or a complete digital fly.

The shape planner and wing rhythm use 1,024 neurons / 42,944 measured connections. The active motor uses 2,048 neurons / 192,267 connections. A 4,096-neuron comparison also passed but showed no accuracy advantage; see [expansion evidence](neuron-expansion.md). All modeled connections are positive; neurotransmitter signs are not yet implemented. Sensory/output mappings are engineered, and rate state resets before each four-step inference. Training uses offline demonstrations and gradient descent. The connectome supplies wiring constraints, not a complete reconstruction of biological physiology.

## Comparison with the cited demos

- [Flyhard’s pilot](https://github.com/MarkUnthank/flyhard/blob/main/docs/pilot-2026-09-09.md) reports trained stationary steering on a substantially larger measured graph with frozen engineered interfaces. Designer Fly follows a related constrained-learning approach at much smaller scale. Our tests are our own, not reproductions of that pilot.
- [Fly / Wirehead’s model notes](https://github.com/mattyhempstead/fly-wirehead/blob/main/docs/model.md) describe approximate spiking dynamics driven by visual input, with some animation mapped to real neural rates. Its swipe gesture is separately choreographed; the authors do not claim learned video preference or validated biomechanics. Its spiking simulation and our trained drawing policy demonstrate different things.
- The previously inspected Supabase laptop video labels itself an animated concept; see [reference review](reference-review.md). That video alone is not evidence of a fly learning database deployment.

There is no single formal “true neural demo” certification. This project qualifies as a trained neural-control demonstration with measurable causal tests. It does not qualify as a biologically validated fly emulation.
