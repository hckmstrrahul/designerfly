# Designer Fly: reference review and learning experiment

Reviewed 11 September 2026. Repository claims are attributed below; no upstream training results were independently reproduced.

## Supabase's exact video

[Supabase, “the fly is deploying databases,” 10 September 2026](https://x.com/supabase/status/2097999894632149229).

The 24.02-second attached video was retrieved through public tweet metadata and inspected at several timestamps. It carries the FLYHARD heading, a fly on a rendered laptop, neural visualization, and a terminal displaying `supabase link` and `supabase db push`. The small footer explicitly reads **ANIMATED CONCEPT**. This is an animated concept demonstration; it does not establish that a fly network selected the commands, learned to type, understood a database, or caused a real deployment. The public main branch of MarkUnthank/flyhard inspected during this review contained steering code and no matching laptop/keyboard controller. Absence in that inspected branch does not establish that no unpublished implementation exists.

## Fly / Wirehead

- [Repository](https://github.com/mattyhempstead/fly-wirehead)
- [Model documentation](https://github.com/mattyhempstead/fly-wirehead/blob/main/docs/model.md)

This project runs approximate spiking dynamics on measured MaleCNS wiring. Phone pixels become engineered visual inputs; some rendered motion is mapped to computed activity. Video selection advances by timer and the leg swipe is separately choreographed. The documented plasticity mechanism changes selected existing connections, but the authors do not establish learned preferences, pleasure, or addiction. A numerical simulation and an animation can coexist without the animation depicting a learned action.

Useful reference: a local native backend feeding a browser view, measured telemetry, source-data provenance, and explicit disclosure of engineered motion. It is not a demonstrated shape-learning policy.

## Flyhard's trained steering experiment

- [Pilot report](https://github.com/MarkUnthank/flyhard/blob/main/docs/pilot-2026-09-09.md)
- [Sparse core](https://github.com/MarkUnthank/flyhard/blob/main/src/flyhard/connectome.py)
- [Frozen input/output interfaces](https://github.com/MarkUnthank/flyhard/blob/main/src/flyhard/motor_policy.py)
- [Training and evaluation](https://github.com/MarkUnthank/flyhard/blob/main/scripts/train_wheel.py)

The reported pilot trains bounded edge gains and neuronal leaks inside a measured graph, with fixed engineered sensory input and motor output mappings. It learns a requested-angle stationary steering skill using teacher-generated demonstrations. The authors report 0/100 held-out targets passed before training and 100/100 afterward in one seed. These are interpolated steering targets, not autonomous visual driving. The source resets rate states between decisions and does not claim biological learning rules. The full graph's forward and custom backward are sparse; a naive dense backward caused a very large temporary allocation.

This is the most useful of the inspected references for a genuine trainable drawing controller. Its trained simulation is meaningfully different from its animated laptop concept.

## Original proposed experiment and implemented scope

A real phase-conditioned coordinate-learning experiment was implemented and verified across three seeds. The current version adds a trained three-joint feedback controller and MuJoCo stylus–paper contact; see [current embodied scope](embodied-prototype.md). It retains a measured 1,024-cell VNC subgraph and frozen interfaces. It does not learn muscle physiology, navigation or novel designs. The original broader proposal below is retained as historical context.

1. Pin and verify [MaleCNS v1.0](https://male-cns.janelia.org/download/) connectivity and annotations. Preserve neuron IDs, edge direction, selection rules, hashes, and CC BY attribution. Any subgraph must be explicitly identified as a subgraph.
2. Define a simple 2D pen environment with x/y position, velocity, and pen contact. Three task IDs select rectangle, circle, or triangle. No prompt encoder or language model is required.
3. Train a connectome-constrained controller to output incremental movement and pen contact. Keep sensory injection and motor decoding fixed for the first experiment so improvement can be attributed to trained parameters within the core.
4. Use geometric demonstrations as training labels. For an autonomous shape-generation claim, the teacher path must not supply successive target positions at inference. Supplying waypoints at inference would instead be disclosed as learned tracing/tracking.
5. Evaluate full closed-loop drawings at held-out sizes, locations, and starting points. Record contour error, closure, completion rate, and time. Compare trained, untrained, core-disabled, and shuffled-connectivity controls across multiple seeds. A working learned policy does not by itself show that biological topology is better than alternatives.
6. Render the actual predicted trajectory, including errors. Drive any neural display from computed model states. Keep a scripted reference path out of the visible result and motor commands.

## Machine feasibility

The locally inspected machine has an M5 Max, 40 GPU cores, and 128 GB unified memory. This supports developing the browser view and running memory-efficient graph experiments. It does not establish training throughput. The inspected Flyhard trainer selects CUDA if available and otherwise CPU; it does not implement a tested Apple GPU path. Benchmark a small forward/backward workload before predicting full training time. No CUDA GPU is available merely because the Mac has many GPU cores.

Successful training would produce an **engineered neural controller built from biological wiring**, not a living fruit fly or a validated emulation of its mind.
