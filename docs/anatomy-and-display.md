# Anatomy and activity

Janelia's colorful CNS images render reconstructed neuron anatomy derived from electron microscopy, segmentation, proofreading, and 3D reconstruction. The colors distinguish cells or groups. A static anatomical image is not a measurement of ongoing neural firing. The project page does not identify the exact renderer used for its two still images; it links Neuroglancer and other viewers.

Sources: [Janelia Male CNS](https://www.janelia.org/project-team/flyem/male-cns-connectome), [official data and skeleton formats](https://male-cns.janelia.org/download/).

## Our device

- The original planner circuit includes 640 VNC intrinsic, 256 VNC sensory and 128 VNC motor cells. The active 2,048-cell motor adds 1,024 intrinsic VNC cells. Both exclude the full central brain and optic lobes. See [neuron expansion](neuron-expansion.md).
- The motor has 1,769 measured soma coordinates and 279 missing locations. Wing mode returns to the original 758 located / 1,024 total cells. We do not invent locations; every cell still participates in inference and the mean-absolute-rate trace.
- Activity mode shows located somas and up to about 1,800 sampled measured graph edges when both endpoints have known positions. These straight lines are connectivity abstractions, not axon trajectories. Blank areas are not evidence of neuronal silence.
- Anatomy mode shows 96 cached MaleCNS SWC skeletons whose body IDs belong to this same circuit. The cached 902699 SWC was checked byte-for-byte against the official v1.0 source during this update. Source-file hashes for all 96 are in `research/results/anatomy-manifest.json`.
- `scripts/prepare-neural-anatomy.mjs` preserves branch points and samples long branches at approximately 4-micron path intervals, producing 105,558 displayed segments. Coordinates remain in the official 8-nm voxel coordinate system until projection. The 3.3 MB asset loads only when Anatomy is selected.
- Anatomy colors reflect annotated class: 23 sensory skeletons (cyan), 63 intrinsic/local-circuit skeletons (purple), and 10 motor skeletons (gold). This is structural anatomy; color does not animate or imply voltage propagation down branches.
- Activity hue encodes signed rate: negative red, zero dark green, positive green. Dot and glow share the exact same hue, including for small values; strength is encoded by opacity and size. Quiet dots use low opacity. Dot size and feathered glow encode magnitude; absolute changes between samples strengthen the glow (8× gain capped at 1). A fixed square-root display curve makes small values visible. There are no rings or invented spikes. A new run or controller source starts without a change boost. The canvas checks for observations every animation frame instead of throttling to 15 fps. The physics client supplies observations at up to 25 Hz; unchanged states remain unchanged.
- Both modes use an interactive orthographic projection of real 3D coordinates. Drag/arrow keys rotate, scroll or +/− zoom, right-drag/Shift-drag or Shift+arrows pan; double-click/Home resets. Two-finger gestures pan and zoom. Mode changes preserve camera and trace history. No missing neurons are added to make a whole-brain silhouette.
- Drawing shows the learned feedback controller's actual rate state; Wings shows the learned circle planner's state, including during drawing. Enabling flapping selects Wings; the in-screen selector lets you inspect either controller without combining their different graphs. Rate values are engineering approximations, not recorded spikes.
- Trace history records new observations only and persists when changing display mode. Both modes retain Drawing controller/Wing rhythm and Live/Paused indications, counts and drawing progress within the screen. Mean strength is the mean absolute rate over all neurons in the displayed controller, with labeled automatic bounds.
- Arrange and Wings are physical-style utility buttons; Activity and Anatomy are physical-style mode buttons. Fly status is plain Departure Mono text at the scene's top left. The old reset-view icon and chassis message box were removed.

## Fly pose and grip

The left foreleg exits laterally beneath the head, with an outward elbow and planted foot. Five support legs remain in a fixed stance. The drawing leg uses the actual three-joint MuJoCo poses. Its segmented tarsus approaches beside a shorter pencil cap and curls around the shaft exterior while preserving bone lengths. The pencil remains rigidly attached; this is not learned free-object grasping.

`research/export_pose_check.py` exports actual learned trajectories. `scripts/check-fly-clearance.mjs` probes support-leg centerlines and sampled mesh vertices against the original thorax, head, eyes and abdomen surfaces, plus sampled drawing-leg vertices over all exported poses. The detector includes an inside-thorax positive control. These are checks of the configured poses, not an exact continuous full-body collision solver or a guarantee for new tasks.

## Future capabilities

Prompt-to-UI drawing is feasible as a hybrid: a separate language/layout planner supplies a drawing specification; a stroke controller executes it. The composition prototype now supports specified positions, scales and pen lifts within a bounded workspace. New stroke families and larger reach require further training/body changes. A language planner's understanding should not be attributed to the fly connectome. See [composition training](composition-training.md).

Walking and simulated flight are demonstrated research directions: [NeuroMechFly](https://neuromechfly.org/) and [FlyBody](https://github.com/TuragaLab/flybody) provide relevant bodies and controllers/tasks. Integration would require a free body, all limb actuators, balance/contact sensing and trained locomotion control; flight additionally needs aerodynamic forces and stabilization. This is a substantial new experiment, not an effect unlocked by adding more neurons to our current model. None of those extensions alone establish a biologically complete fly.
