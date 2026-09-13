# Designer Fly

A fly-connectome-based neural controller trained to trace drawings with a simulated foreleg.

Create a UI, text, emoji or freehand drawing and watch the fly trace its paths.
The neural displays show controller activity and selected anatomical neuron structures.
Drawing paths are supplied by the editor; the trained controller moves the physical foreleg
along them rather than independently inventing drawings or understanding their content.

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

- **Device modes:** Draw UI, Text and Emoji open separate views and retain separate canvases during the session. Shape buttons live inside Draw UI; Text, Emoji and Pen are icon-only tools below the shape palette. Pen draws directly on the composition rather than opening another mode.
- **Draw UI:** compose up to 128 pen strokes. Add rectangles, squares, circles,
  ellipses and triangles; move or resize them directly on the sheet.
  The initial canvas contains a detailed editorial wireframe with rounded cards,
  landscape thumbnails, content lines and a small FLY masthead.
- **Pen:** in Draw UI, select Pen and drag on the canvas with a mouse, stylus or
  finger. Each release adds one stroke. Use New for a blank sheet, then **Draw**
  to send the paths to the fly. Tiny jitter is simplified and oversized
  strokes are fitted to the supported area, with at most 256 points per stroke.
  This uses supplied paths and the existing motor, not a sketch-recognition model.
  Very small details or tightly packed scribbles may not reproduce accurately.
- **Text:** in Text mode, enter up to 40 characters, including spaces and line
  breaks. Supports A–Z, 0–9 and `. ! ? -`; lowercase becomes uppercase. Long
  lines wrap at seven characters. The live preview sits at the bottom right; **Draw** sends it directly to the fly. In Draw UI, the compact monospace text panel adds lettering to the visible canvas.
  The device Text mode uses its own sheet; the sidebar Text tool adds to the
  current composition as a selectable group. New, Delete, Clear all and Reset sit beside the studio heading.
  Reset appears when the canvas differs from the default UI example.
  The original single-line alphabet is supplied vector geometry, not learned
  language or a newly trained text model. The existing 2,048-neuron motor follows
  these paths through the same contact-based physics as other drawings.
- **Emoji:** choose from 12 designs: Smile, Wink, Surprise, Cool, Heart, Star,
  Laugh, Love, Sleepy, Sad, Sun and Lightning. These are original
  minimal stroke drawings, executed by the same physical motor. The device Emoji
  mode draws the selected emoji directly with **Draw**. The Draw UI sidebar adds each emoji as one group that moves, resizes and deletes together.
- **Speed:** cycle through 1×, 3× and 6× simulation time. Each update runs 2, 6 or
  12 full control steps. The fixed physics timestep, feedback inference and every
  contact/ink sample are preserved. This is faster execution of the same
  simulation, not a controller trained to move faster in physical time. The orange
  Speed button shows 1×, 3× or 6× above its white LEDs; the caption stays SPEED.
  Wing inference uses the same speed-scaled clock while drawing or idle. Wing
  motion, NL–01 and NS–01 share each inference sample and its simulation timestamp;
  changing speed preserves phase instead of restarting the wing cycle.
- **Camera:** cycles Angled → Paper close-up → Overhead. The angled view is the
  initial default. The chosen preset is saved locally and restored after reloads
  and simulation resets. Manual orbit/zoom remains available; only the preset
  selected with the button is saved. NS–01 starts in a centered frontal view.
- **Wings:** run the learned rhythm used to animate the wings.
- **Drawing 01 / Drawing 02:** select the motor or wing controller on Neural Link.
  Drawing 02 starts wings; Drawing 01 stops them. Both neural displays follow the
  selected controller. Drag to rotate,
  right-drag or Shift-drag to pan, scroll/pinch to zoom, double-click to reset.
  Focus the neural canvas for arrow-key rotation, Shift+arrow panning, `+`/`−`
  zoom and Home reset. The fly scene also supports rotate, pan and zoom.

In Draw UI, focused shapes support arrow keys to move, Shift+arrows for larger moves,
and Delete to remove. Shapes stay inside a reachable 0.88 × 0.88 model-mm region
on the larger paper. Shapes, supplied lettering, grouped emojis and freehand paths
can be combined on the same sheet.

Canvas editing supports Delete/Backspace, Undo (Cmd/Ctrl+Z), and Redo (Cmd/Ctrl+Shift+Z or Ctrl+Y). Toolbar Undo/Redo also restore additions, grouped edits, clear/reset and completed pen strokes; each drag is one history step.

The drawing action is labeled **Draw** in every mode. **Reset** restores the default
UI example; **Clear all** empties the current canvas. Hardware button housings remain
fixed on press, with a subtle inset face movement. Scroll and pinch zoom respond
faster across all three displays, with a range of 0.15×–12×.

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
six square studio/shape buttons in this layout.

**About this experiment** opens a modal with the method, limitations, validation
figures and source credits. Project information uses locally hosted Inter; device
readouts retain Departure Mono.

## How the fly actually works

1. **A learned path.** A 1,024-neuron network receives the selected shape and a
   generic phase encoding. Its output is a canonical pen path. During live
   inference it does not call the analytic shape teacher used in training.
2. **A specified layout.** Draw UI applies an explicit position/size transform. Rounded UI details and lettering use supplied polylines with arc-length interpolation, bypassing the three-shape planner but retaining the trained motor and physics.
   A sequencer supplies travel, lowering, drawing and lifting phases. These
   decisions are ordinary application code.
3. **Neural feedback control.** The active **2,048-neuron, 192,267-connection** motor
   network reads the intended point, joint angles and velocities, tip error and
   contact force. It produces three incremental rotary actuator commands.
4. **Physical motion.** MuJoCo integrates the reduced foreleg and attached stylus.
   The next observation comes from the resulting body state. Ink appears only
   when the physical tip contacts the paper during a drawing phase. The live
   control step uses no inverse kinematics.

The original planner and rate motor are four-step rate networks based on a selected **MaleCNS v1.0**
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

Enabling S–01 Wings selects Motor on NL–01 and shows the actual 1,024-neuron
wing rhythm on both monitors, even during drawing. NL–01 has no separate Wings
button. Counts follow the selected network; wing rates are not relabeled as spikes.

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
.venv/bin/python research/test_paper_coordinates.py
.venv/bin/python research/validate_freehand.py
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
choices, not new anatomical measurements. The paper is 1.15 × 1.15 model units,
with matching collision bounds; the drawing region is now 0.88 × 0.88.
This makes the drawing fill more of the paper with the expanded region checked in physics.

The physical check covers the UI example, `HELLO` / `WORLD`, the alphabet,
numbers, supported punctuation and 12 minimal emoji designs. All sixteen sessions completed with 100% contact
on sampled drawing frames. XY tracking RMSE ranged from 0.00606 to 0.00879 model
units. See [the recorded results](research/results/detailed-strokes-validation.json).
These are smoke checks, not a comprehensive handwriting benchmark or a guarantee
for every arrangement. Letter geometry is original code in `lib/lettering.ts`;
no additional font dataset or text training was used.

## Deployment

The production frontend is [designerfly.vercel.app](https://designerfly.vercel.app/).
Its persistent MuJoCo physics service runs on
[Railway](https://physics-production-198a.up.railway.app/health), deploying from
`main` with `Dockerfile.physics`. Docker installs the Python dependencies and starts
`research/server.py`; visitors do not need to run a local physics service.

`npm run build` produces the frontend in `dist`. For local development,
`npm run dev` starts the frontend and physics service together; `npm run physics`
starts only the Python backend. `npm run dev` automatically reloads Python source
changes. Vite proxies local API requests through `/physics`.

To connect the deployed frontend:

1. Run the repository on a persistent Python 3.12 host with `research/requirements.txt`
   installed. Keep the tracked `research/data`, model checkpoints and `public` assets.
2. Start `python research/server.py` with `HOST=0.0.0.0`, the host's assigned `PORT`,
   and `ALLOWED_ORIGINS=https://designerfly.vercel.app`. Use one process/replica:
   drawing sessions currently live in memory, and the service allows eight sessions.
3. Verify the backend's HTTPS `/health` endpoint returns JSON with `ready: true`.
4. Set `VITE_PHYSICS_URL` in Vercel to that HTTPS backend URL (no `/physics` suffix),
   then rebuild/redeploy. Without this setting, local development uses `/physics`.

Production `VITE_PHYSICS_URL` is `https://physics-production-198a.up.railway.app`.
Both the trained and Spikes controllers passed deployed session creation and
12-frame stepping smoke checks, with production-origin CORS verified. These checks
verify hosting connectivity; physical accuracy is covered by the validation reports.

Drawing playback prefetches up to 20 display samples per request (four for the
initial response), then consumes them on the browser clock at 1×, 3× or 6×.
Each sample includes its corresponding neural state, so telemetry follows the
visible movement. Queues are bounded, reset with the drawing session, and stop
advancing in hidden tabs. Compressed responses reduce transfer size. The physics
service is configured for Singapore to reduce network distance for users in India.
Network stalls or server load can still interrupt playback; buffering is not a
retraining change or a guarantee of real-time performance on every connection.

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


## Experimental spiking circuit (feature branch)

NL–01 has **Motor** and **Spikes** selectors. Motor selects the trained rate
controller; Spikes selects the persistent spiking foreleg controller. Both remain
available during drawing. New drawings default to Motor for cleaner tracing. Spikes remains an experimental
option and can produce wavier lines. The square info button explains both controllers
and the NL–01 / NS–01 displays without interrupting the drawing. During a switch, the existing animation continues until matching
new samples arrive; the display loop stays mounted. Changes apply at the next requested playback batch,
preserving the body, paper, stroke index and path phase. Already buffered motion
finishes first. Neural samples retain their actual source during the handoff.
Switching can briefly disturb pen contact; it is not equivalent to a controller
trained specifically for seamless handoffs.

Each spiking drawing session owns its membrane voltages, synaptic currents,
refractory periods and firing-rate history. Foreleg sensory feedback is encoded through a fixed random projection onto 256
sensory cells (40 mV offset, clipped to 0–150 mV); other cells receive a documented
12 mV tonic drive. An offline-trained interface decoder maps actual motor-neuron firing traces to the
three rotary actuator commands from 128 motor-cell firing rates and their temporal
differences; it has no direct observation-to-action shortcut.
The original readout used offline rate-motor demonstrations. Its UI refinement uses
offline inverse-kinematics feedback labels and a conservative readout blend; neither
teacher runs during drawing.
Internal anatomical weights remain frozen. The spiking mode requests a 0.004-unit
lower contact reference to improve paper contact; this is a task-pressure calibration,
not a direct actuator correction. Supplied paths use 1.2× drawing duration and
learned shapes use 1.6× to allow for filtered spiking feedback. Both retain the
same physical and neural timestep. This is trained motor interfacing, not
learning-free drawing or a biological reproduction of pencil use.

The API and UI enable spiking drawing only when the physical validation report
passes and its graph/checkpoint and runtime-code SHA-256 hashes match the installed artifacts.
`/session` and `/composition` accept `controller: "spiking"`; omitted means the
original trained controller. State persists over the 20 ms physics control interval
and throughout pen travel, lowering, drawing and lifting. The 1×/3×/6× speed control
advances matching neural and physical time, rather than skipping neural simulation.

The experimental circuit retains the 2,048-neuron graph and joins official MaleCNS neuron-level
transmitter predictions by body ID. With confidence >= 0.5, it assumes ACh is
excitatory and GABA/glutamate inhibitory: 1,128 excitatory, 793 inhibitory, and 127
unresolved cells. Receptor exceptions and modulatory effects are not modeled.
Of the unresolved cells, 73 are below the confidence threshold and 54 have
unmodeled transmitter labels. All 2,048 selected neurons lack synaptic receptor
annotations in this source. Unresolved cells retain their anatomy but contribute
zero fast synaptic current.
Predicted signs are assumptions, not established biological effects at every edge.

Weights are measured synapse counts times presynaptic sign times a global 0.15 mV
scale; there are no learned per-edge gains or row normalization. Persistent LIF
state uses 1 ms steps, 20 ms membrane and 5 ms synaptic time constants, a threshold
15 mV above rest, reset to rest, and a 2 ms refractory period. A spike affects
postsynaptic current at the next step. These are exploratory engineering parameters,
not calibrated fly physiology. The display shows firing rates smoothed over 100 ms,
normalized to 100 Hz and saturated above that value. The trace is the mean of these
normalized display values, not a biological spike recording. A constant-stimulus
diagnostic remains available through `/spiking` endpoints for circuit tests; the
NL–01 Spikes button uses physical feedback and controls the pencil.

To reproduce the compact annotated graph, download the official file recorded in
`research/results/spiking-manifest.json` to `research/data/neurotransmitters.feather`,
then run `.venv/bin/python research/prepare_spiking.py` (the original pinned
`annotations.feather` is also needed for the receptor audit). Source and original graph
SHA-256 hashes, assumptions, and coverage are recorded in that manifest. The compact
`circuit-spiking.npz` is included; the full annotation download is not required to run.
`research/train_spiking_motor.py` reproduces the original base readout and rewrites
the installed checkpoint; doing so invalidates the acceptance gate until revalidated.
For the current UI refinement, use the preserved `spiking-motor-base.npz` and the
candidate-only training workflow in [UI motor training](docs/ui-motor-training.md). Run
`.venv/bin/python -m unittest discover -s research -p 'test_spiking*.py'` for
annotation provenance, persistent state, fixed weights, physical actuation,
contact-only ink and session isolation.

The default Draw UI example now uses an evenly spaced **THE TIMES OF FLIES**
masthead, search, feature image, article cards, and footer. Desktop canvas previews
fit their available width and height; the stacked tablet layout retains scrolling.
The physical drawing scale is expanded from 0.44 to 0.52 while keeping paper margins.
A complete 46-stroke run finished with 99.95% drawing-contact samples and 0.0091
model-length-unit tracking RMSE. This is one layout check, not a new general
biological accuracy claim or a replacement for the historical checkpoint reports.

The current spiking motor acceptance run covers nine cases: the newspaper UI,
lettering, two emojis, two freehand paths, and the three learned shape families.
All complete with 97.608–100% drawing contact, zero travel contact, and tracking
RMSE 0.01958–0.03026 model-length units. The newspaper's 46 strokes reach 99.815%
contact and 0.02736 RMSE, with at least 98.96% contact on every individual stroke.
A disturbance trial passes; removing feedback raises error to 0.57952, and removing
the recurrent circuit raises it to 1.53741. These tests demonstrate task dependence
on feedback and the fixed circuit, not biological fidelity or superiority to
alternative architectures. See `research/results/spiking-motor-validation.json`.

The UI readout refinement reduced measured roughness by **12.64%** and cross-track
error by **12.78%** on a separately locked seven-fixture quality test. Contact rose
from 99.609% to 99.835%. These are fixture averages: vertical and diagonal path
accuracy regressed, and not every contact metric improved. Original circuit weights
and the sensory projection remain unchanged. The original rate-based **Motor**
mode is unchanged; choose **Spikes** in NL01 to use this readout. Training details,
reproduction, retained baseline, and limitations are in
[UI motor training](docs/ui-motor-training.md).


## Research archive

The rejected receptor-calibration experiments and their reports remain on the
[`feature/spiking-connectome` research branch](https://github.com/hckmstrrahul/designerfly/tree/feature/spiking-connectome).
They are not part of the deployed motor controller. Main retains the validated
trained rate motor and Spikes controller, including their physical acceptance
reports and reproducible UI readout training.
