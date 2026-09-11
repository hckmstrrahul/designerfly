# Third-party sources

Designer Fly's original application and research code is MIT licensed. The
following materials keep their upstream licenses.

## MaleCNS / FlyEM — CC BY 4.0

Source: https://male-cns.janelia.org/ and https://male-cns.janelia.org/download/

Credit: FlyEM / HHMI Janelia Research Campus and the MaleCNS collaboration,
including the University of Cambridge, MRC Laboratory of Molecular Biology,
and Google Research. Please follow the dataset's current citation instructions
when using it in research.

License: https://creativecommons.org/licenses/by/4.0/

We use the **v1.0** neuron annotations, measured synapse-count connectivity, and
selected SWC neuron skeletons. Modifications include subgraph selection,
weight normalization, learned gains/biases/leaks, simplified skeleton rendering,
and browser exports. Selected `.npz`/Feather data, derived circuit JSON,
checkpoints, and neuron-anatomy JSON retain CC BY 4.0 attribution. Dataset and
source-file hashes are in `research/results/graph-manifest*.json`; SWC provenance
is in `research/results/anatomy-manifest.json`. No endorsement is implied.

The bulk Feather downloads and local skeleton cache are not in the repository.
`research/download.sh` downloads the original connectivity and annotations;
preparation verifies their recorded hashes.

## NeuroMechFly / FlyGym — Apache 2.0

Source: https://github.com/NeLy-EPFL/flygym

Credit: Neuroengineering Laboratory (NeLy), EPFL, and FlyGym contributors.
Meshes and rig information are pinned to commit
`38c8ec61034cd59bc5ba0de20688d4a3c0000d60`.

The original license is in `public/models/fly/LICENSE`; source paths and hashes
are in `public/models/fly/provenance.json`. `research/assets/` also derives from
this source. Scene materials, colors, mirrored geometry, stance and pencil grip
are modified. Our reduced MuJoCo foreleg is not the complete NeuroMechFly body.

## Departure Mono — SIL Open Font License 1.1

Source: https://departuremono.com/ — Helena Zhang and font contributors.
The bundled font's license and version information are in
`public/fonts/departure-mono/`. The font has not been modified.

## Software dependencies

- [Three.js](https://github.com/mrdoob/three.js) — MIT; 3D rendering.
- [MuJoCo](https://github.com/google-deepmind/mujoco) — Apache 2.0; physics.
- [PyTorch](https://github.com/pytorch/pytorch) — BSD-style; training.
- [Lucide](https://lucide.dev/license) — ISC; interface icons.
- React, Vite, NumPy, SciPy, PyArrow and FastAPI retain their respective licenses.

Exact JavaScript versions are in `package-lock.json`; Python versions are in
`research/requirements.txt`. These dependencies are installed separately.

## References, not bundled code

[Fly / Wirehead](https://github.com/mattyhempstead/fly-wirehead),
[Flyhard](https://github.com/MarkUnthank/flyhard), and Supabase's fly animation
informed the reference review. Their demo results are not Designer Fly's results.
See `docs/reference-review.md` for the distinction.

## Inter

Inter by Rasmus Andersson and contributors is licensed under SIL Open Font License 1.1.
Source: https://github.com/rsms/inter
Bundled license: `public/fonts/inter/LICENSE.txt`. Used for project information and the experiment modal.
