# Designer Fly

A little fly at a drawing desk, inside a pair of hardware-inspired instruments.
Choose a shape, or arrange a small wireframe and watch it draw. The second device
lets you explore the controller's activity and some of the neurons it is based on.

Built by [@hckmstrrahul](https://github.com/hckmstrrahul).

**This is a trained, embodied neural prototype. It is not a complete biological
fly simulation.** The drawing controller uses measured fruit-fly connectivity,
learned parameters, sensory feedback and a reduced physical foreleg. The layout
editor, task sequencing, body constraints and sensory interfaces are engineered.

## Try it locally

You need Node.js 22.13 or newer, Python 3.12, and [uv](https://docs.astral.sh/uv/).

```sh
git clone https://github.com/hckmstrrahul/designerfly.git
cd designerfly
npm ci
uv --native-tls --cache-dir .cache/uv venv --python 3.12 .venv
uv --native-tls --cache-dir .cache/uv pip install --python .venv/bin/python -r research/requirements.txt
npm run dev
```

Open **http://127.0.0.1:5190/**. The command starts the frontend and a Python
physics service on port 5192. Trained checkpoints, selected circuits and display
assets are included, so you do not need the full dataset or a training run.

There are no API keys, paid inference calls or database dependencies. Training
and inference run on your machine. CPU speed affects how fast the simulation
can advance. If the backend stops, drawing stops too; there is no fallback animation.

In development, the Agentation button at bottom right lets you select an element,
write feedback, and copy annotations to paste into your coding agent. It is excluded
from production. Automatic delivery requires a separately configured Agentation MCP
server; the default toolbar uses local copy/paste.

## Controls

- **Rectangle / circle / triangle:** draw on a fresh sheet. Press the selected shape again to stop, clear the paper, stop flapping, and restore the initial physical pose and camera. Keyboard: `1`, `2`, `3`. Arrange mode keeps adding shapes instead.
- **Arrange:** compose up to 96 pen strokes. Add rectangles, squares, circles,
  ellipses and triangles; move or resize them directly on the sheet.
  **UI Example** loads a detailed editorial wireframe with rounded cards,
  landscape thumbnails, content lines and a small FLY masthead.
- **Text:** inside Arrange, enter up to 20 characters, including spaces and line
  breaks. Supports A–Z, 0–9 and `. ! ? -`; lowercase becomes uppercase. Long
  lines wrap at seven characters. Text sits beside UI Example; opening it replaces
  the canvas and shape toolbar with a large input. Choose **Preview lettering**,
  then **Draw study**.
  The original single-line alphabet is supplied vector geometry, not learned
  language or a newly trained text model. The existing 2,048-neuron motor follows
  these paths through the same contact-based physics as other drawings.
- **Speed:** cycle through 1×, 2× and 4× simulation time. Each update runs 2, 4 or
  8 full control steps. The fixed physics timestep, feedback inference and every
  contact/ink sample are preserved. This is faster execution of the same
  simulation, not a controller trained to move faster in physical time. The orange
  Speed button starts at 1×; one, two or three white LEDs indicate the speed.
- **Wings:** run the learned rhythm used to animate the wings.
- **Drawing 01 / Drawing 02:** select the motor or wing controller on Neural Link.
  Drawing 02 starts wings; Drawing 01 stops them. Both neural displays follow the
  selected controller. Drag to rotate,
  right-drag or Shift-drag to pan, scroll/pinch to zoom, double-click to reset.
  Focus the neural canvas for arrow-key rotation, Shift+arrow panning, `+`/`−`
  zoom and Home reset. The fly scene also supports rotate, pan and zoom.

In Arrange, focused shapes support arrow keys to move, Shift+arrows to resize,
and Delete to remove. Shapes stay inside a reachable 0.8 × 0.8 model-mm region
on the larger paper. This is a geometric wireframe tool: no text or arbitrary paths.

## The devices

- **Simulator (S–01):** the physical drawing scene and hardware-style controls.
- **Neural Link (NL–01):** located neurons, signed activity colors, an average
  activity trace, controller selection, stylus contact and drawing progress.
  With no samples, the trace shows a gray placeholder rather than fabricated activity.
- **Neural Spectrum (NS–01):** measured neuron skeletons with activity-driven brightness.

Desktop fits the devices on one screen. Heights grow on taller displays, up to
1,040 px for the simulator; smaller viewports scale the group to fit. On tablets,
the two neural devices share a width. Narrow screens use a wider, vertically
scrollable stack with cables between adjacent devices. Vertical swipes over the
scenes scroll the mobile page. The simulator's circular controls sit above its
four evenly sized shape/Arrange buttons in this layout.

**About this experiment** opens a modal with the method, limitations, validation
figures and source credits. Project information uses locally hosted Inter; device
readouts retain Departure Mono.

## How the fly actually works

1. **A learned path.** A 1,024-neuron network receives the selected shape and a
   generic phase encoding. Its output is a canonical pen path. During live
   inference it does not call the analytic shape teacher used in training.
2. **A specified layout.** Arrange applies an explicit position/size transform. Rounded UI details and lettering use supplied polylines with arc-length interpolation, bypassing the three-shape planner but retaining the trained motor and physics.
   A sequencer supplies travel, lowering, drawing and lifting phases. These
   decisions are ordinary application code.
3. **Neural feedback control.** The active **2,048-neuron, 192,267-connection** motor
   network reads the intended point, joint angles and velocities, tip error and
   contact force. It produces three incremental rotary actuator commands.
4. **Physical motion.** MuJoCo integrates the reduced foreleg and attached stylus.
   The next observation comes from the resulting body state. Ink appears only
   when the physical tip contacts the paper during a drawing phase. The live
   control step uses no inverse kinematics.

Both networks are four-step rate networks based on a selected **MaleCNS v1.0**
ventral nerve cord subgraph. Training changes measured-edge gains, neuron biases
and leaks. Sensory projection and motor decoder weights are frozen. Network state
resets each inference. Training is supervised learning from shape examples and
offline actuator demonstrations, not reinforcement learning or online learning
from the user's drawings.

The motor expansion retains all original cells and adds connected intrinsic VNC
neurons, selected without drawing labels. It preserves every measured connection
within the selected graph. Expanded models use positive softplus gains to transfer
existing effective weights without clipping when row normalization changes.
Neurotransmitter predictions and biologically calibrated dynamics are not included.

## What the neural screen means

**Activity** shows located cell bodies and sampled connections. Red encodes negative
rates and green positive rates, with dark green at zero; this sign is not a
neurotransmitter label. Every located cell keeps a pale 20%-opacity base dot.
Color opacity, dot size and a restrained same-color glow show magnitude; changes
between samples strengthen the glow. A fixed square-root display curve reveals
small values, with 8× gain on the change component. Unchanged values remain still. The bottom
trace is mean absolute rate across every neuron, including cells without positions.

Enabling wings on either device selects the 1,024-neuron wing controller on both
live monitors, even during drawing. The NL–01 Drawing 01 button stops flapping and
returns to the motor controller. Counts follow the selected network.

**Neural Spectrum (NS–01)** shows the same 96 measured 3D skeletons in a separate
interactive view below Neural Link. A stable hue identifies each neuron; opacity and
line thickness follow the magnitude of its actual controller rate. This is a
cell-level activity overlay, not simulated propagation along branches. All live values are computed model states,
not recordings of a biological fly's spikes.

## What it can and cannot do

It draws three learned shape families, positioned compositions and physical pen
lifts in a bounded workspace. Its controller has been checked against small
disturbances. The source includes comparison runs and tests that remove neural
connections or sensory feedback.

The fly's body is fixed; only one three-joint foreleg is physically controlled.
The pencil is attached, not freely grasped. Other legs are posed visually. Wing
motion is neurally driven animation without aerodynamics. It cannot walk, fly,
understand a prompt or design an arbitrary interface. A task depending on measured
wiring is not evidence that this wiring outperforms a random graph, or that the
model reproduces a real fly's motor physiology.

## Results and reproducibility

The 2,048-neuron motor passed **34 strokes across eight independent layouts**,
including the search/feed preset, with no paper contact during travel. Worst
stroke RMSE was **0.01529 model mm**, below the declared 0.035 threshold; each stroke
had more than 95% drawing contact. Single shapes and disturbance recovery passed.

More neurons did **not** clearly improve accuracy: the matched 1,024-neuron motor
had worst stroke RMSE 0.01522. These are one-seed warm-start comparisons, not a
general scaling result. We kept 2,048 as the requested expansion. See
[the expansion experiment](docs/neuron-expansion.md) and the machine-readable
`research/results/expansion-*.json` files for all sizes, timings and criteria.

Earlier planner refinement reduced rectangle maximum edge deviation from 0.06492
to 0.008645 in normalized path units. These coordinate units differ from physical
tracking error. Historical results remain in the repository and are labeled
separately from the active motor experiment.

Run the checks:

```sh
npm test
npm run lint
npm run build
.venv/bin/python research/test_telemetry.py
.venv/bin/python research/test_speed.py
.venv/bin/python research/test_physics.py
.venv/bin/python research/test_composition.py
.venv/bin/python research/validate_detailed_strokes.py
.venv/bin/python research/evaluate_expansion.py
node scripts/check-fly-clearance.mjs research/results/expansion-poses-2048.json
```

Telemetry tests compare exported actions and every displayed neural value with
PyTorch. Speed tests require identical physical trajectories across batch sizes.
Mesh-clearance checks sample configured trajectories; they are not a continuous
whole-body collision guarantee.

To rebuild the larger graphs and repeat the comparison:

```sh
sh research/download.sh
.venv/bin/python research/expand_circuit.py
.venv/bin/python research/train_expansion.py --steps 2400
.venv/bin/python research/evaluate_expansion.py
```

The raw downloads total about 1 GB and are hash-checked. The comparison warm-starts
from the included original composition checkpoint. For the earlier training
stages and their limitations, read [the neural experiment](docs/neural-experiment.md),
[embodied prototype](docs/embodied-prototype.md) and
[composition training](docs/composition-training.md).

## Detailed strokes and scene

S–01 now uses a dark grid surface, selective glossy cuticle and eye materials,
stronger thorax stripes and warmer leg/abdomen colors. These are artistic material
choices, not new anatomical measurements. The paper is 1.07 × 1.07 model units,
with matching collision bounds; the reachable drawing region remains 0.8 × 0.8.
This makes the drawing fill more of the paper without claiming extra motor reach.

The physical check covers the UI example, `HELLO` / `WORLD`, the alphabet,
numbers and supported punctuation. All four sessions completed with 100% contact
on sampled drawing frames. XY tracking RMSE ranged from 0.00635 to 0.00736 model
units. See [the recorded results](research/results/detailed-strokes-validation.json).
These are smoke checks, not a comprehensive handwriting benchmark or a guarantee
for every arrangement. Letter geometry is original code in `lib/lettering.ts`;
no additional font dataset or text training was used.

## Deployment

Nothing is deployed by the local commands. `npm run build` produces the frontend
in `dist`. **Vercel hosting of the static frontend alone will not run the physics
service.** A deployed version needs a separately hosted Python backend and an API
proxy, or a future browser physics port. The current app uses Vite's `/physics`
proxy and intentionally binds its backend to localhost.

## Sources and licenses

- **[MaleCNS / FlyEM](https://male-cns.janelia.org/)** — v1.0 connectivity,
  annotations and selected neuron skeletons. FlyEM / HHMI Janelia and the MaleCNS
  collaboration. **CC BY 4.0**. Subgraphs, normalized weights, trained checkpoints
  and display exports are derived modifications; source hashes and body IDs are
  retained in the graph and anatomy manifests.
- **[NeuroMechFly / FlyGym](https://github.com/NeLy-EPFL/flygym)** — fly meshes and
  rig, pinned to `38c8ec61034cd59bc5ba0de20688d4a3c0000d60`. NeLy, EPFL and contributors.
  **Apache 2.0**. Materials, stance, mirrored geometry and pencil grip are adapted.
- **[Departure Mono](https://departuremono.com/)** — Helena Zhang; **SIL OFL 1.1**.
- **[Inter](https://github.com/rsms/inter)** — Rasmus Andersson and contributors; **SIL OFL 1.1**.
- **[Lucide](https://lucide.dev/)** — interface icons; **ISC**.

## Open use

The original code is [MIT licensed](LICENSE): you can use, study, modify, share,
and build on it, including commercially. Keep the copyright and license notice
with copies or substantial portions of the code. The software comes without warranty.

This permission does not replace the licenses of the datasets, trained data
exports, meshes, fonts, or other third-party materials. Keep their attribution
and comply with the source licenses listed above.

Third-party materials retain their own
licenses; see [full notices](THIRD_PARTY_NOTICES.md). References to Fly / Wirehead,
Flyhard and Supabase are discussed in [the reference review](docs/reference-review.md).
Their demos and results should not be confused with this experiment.
