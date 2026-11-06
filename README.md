# Designer Fly

A fly-connectome-based neural controller trained to trace drawings with a simulated foreleg. Create a UI composition, text, emoji or freehand path, then watch the physical pencil and neural-activity displays respond.

[Try the hosted app](https://designerfly.vercel.app/) · [Watch the demo](https://youtu.be/ekJNq7rWOOA) · [Model capabilities](docs/model-capabilities.md)

[![Designer Fly demonstration](https://img.youtube.com/vi/ekJNq7rWOOA/hqdefault.jpg)](https://youtu.be/ekJNq7rWOOA)

**This is an embodied neural prototype, not a complete biological fly simulation.** The editor supplies drawing paths; the controller follows them. It does not invent drawings or understand their content.

## Run locally

Requires **Node.js 22.13+**, **Python 3.12** and [uv](https://docs.astral.sh/uv/).

```sh
git clone https://github.com/hckmstrrahul/designerfly.git
cd designerfly
npm ci
uv --native-tls --cache-dir .cache/uv venv --python 3.12 .venv
uv --native-tls --cache-dir .cache/uv pip install --python .venv/bin/python -r research/requirements.txt
npm run dev
```

Open [127.0.0.1:5190](http://127.0.0.1:5190/). The development command starts Vite and a Python physics service on port 5192. Checkpoints, selected circuits and display assets are included; running the app needs no training run, full dataset download, API key or database.

Physics and inference run on your machine. CPU speed affects playback; if the physics service stops, drawing stops.

## Use the studio

| Tool | What it does |
| --- | --- |
| **Draw UI** | Add, move and resize shapes or compose up to 128 strokes. |
| **Pen** | Draw freehand with a mouse, stylus or finger, then send the paths with **Draw**. |
| **Text** | Trace up to 40 characters; supports A–Z, digits and `. ! ? -`. |
| **Emoji** | Choose one of 12 original stroke designs. |
| **Motor / Spikes** | Select the trained rate controller or experimental spiking controller in NL–01. |
| **Speed** | Play at 1×, 3× or 6× while keeping physical and neural samples aligned. |

Device modes retain separate canvases during the session. Text and emoji tools inside Draw UI add movable groups to the current composition. Tiny details and tightly packed strokes may not reproduce accurately.

## What is simulated

A reduced MuJoCo foreleg moves a pencil using sensory feedback and a 2,048-neuron subgraph derived from **MaleCNS v1.0** connectivity. A separate learned planner produces rectangle, circle and triangle paths; lettering, UI details and freehand drawings supply their own paths to the same motor and physics. Ink appears only when the physical tip contacts the paper during drawing.

The body is fixed, the pencil is attached, and only one three-joint foreleg is physically controlled. Other legs are posed visually; wing motion has no aerodynamic simulation.

- **Motor** is the default trained rate controller. Training adjusts measured-edge gains, biases and leaks; its sensory projection and motor decoder are frozen. Training uses offline demonstrations, not online learning from your drawings.
- **Spikes** is an experimental persistent spiking circuit with fixed internal anatomical weights and an offline-trained motor readout. It can draw wavier lines. Runtime acceptance depends on a matching physical-validation report and artifact hashes.
- **Neural Link** displays computed controller activity. **Neural Spectrum** overlays cell-level activity on selected measured neuron skeletons. These are model states, not recordings of biological spikes or simulated propagation along individual branches.

The task planner, sensory interfaces, constraints and display mappings are engineered. Task dependence on measured wiring does not establish biological fidelity or superiority over other network architectures. See [anatomy and display](docs/anatomy-and-display.md) and [model capabilities](docs/model-capabilities.md) for interpretation and limits.

## Development and validation

```sh
npm test
npm run lint
npm run build
.venv/bin/python research/test_telemetry.py
.venv/bin/python research/test_physics.py
.venv/bin/python research/test_composition.py
.venv/bin/python -m unittest discover -s research -p 'test_spiking*.py'
```

`npm run build` creates the frontend in `dist/`; `npm run physics` starts only the Python service. Physical evaluation, training commands and recorded metrics are documented separately:

| Guide | Covers |
| --- | --- |
| [Embodied prototype](docs/embodied-prototype.md) | Physical foreleg, feedback and validation. |
| [Composition training](docs/composition-training.md) | Paths, pen lifts and multi-stroke drawings. |
| [Neuron expansion](docs/neuron-expansion.md) | Circuit sizes, matched comparisons and reproduction. |
| [UI motor training](docs/ui-motor-training.md) | Spiking readout, retained baseline and quality limits. |
| [Neural experiment](docs/neural-experiment.md) | Earlier training stages and assumptions. |
| [Validation results](research/results/) | Machine-readable reports and manifests. |

## Hosting

The hosted app uses a Vercel frontend and a persistent Railway Python service built with [Dockerfile.physics](Dockerfile.physics). To host your own copy, run `research/server.py` with Python dependencies, tracked data and checkpoints, `HOST=0.0.0.0`, the assigned `PORT` and `ALLOWED_ORIGINS` set to your frontend origin. Use one process/replica: sessions live in memory, with a limit of eight.

Verify the backend's HTTPS `/health` endpoint returns `ready: true`. Set frontend build variable `VITE_PHYSICS_URL` to that backend origin, without a `/physics` suffix, and rebuild. Local development uses Vite's `/physics` proxy. Network and server load can interrupt playback.

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
