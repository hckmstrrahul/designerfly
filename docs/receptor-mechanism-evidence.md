# Targeted receptor-supported proprioceptive gating

**Correction (2026-09-13):** The earlier same-name SNpp38 crosswalk below was invalid: those MaleCNS cells correspond to MANC wing proprioceptors. Its zero/one-edge conclusions are superseded by [the original-ID audit](receptor-connectivity-followup.md). Public recordings are now available locally and [calibration has run](receptor-calibration.md). Historical audit sections below are retained for provenance, not current conclusions.

Research notes, 2026-09-13. This specifies a bounded experimental addition, not a complete biological receptor model.

## Evidence boundary

Dallmann et al. report Rdl/GABA-A expression in **both claw and hook** proprioceptors. Hook signals are suppressed during self-generated movement, whereas claw and club signals persist. GABAergic 9A neurons target hook axons; the discussion interprets inhibition as axonal shunting and reduced release. The corresponding claw inputs are largely 19A, with unresolved function. Thus receptor presence alone does not explain behavioral selectivity. The study does not supply fitted receptor conductances, chloride reversal potentials, or release kinetics for our simulator. Its calcium observations cannot directly specify millisecond spike suppression. [Primary paper, Fig. 1, Figs. 3–4 and Discussion](https://doi.org/10.1038/s41586-025-09554-2), [author-hosted text](https://faculty.washington.edu/tuthill/docs/Dallmann_et_al-2025-Nature.pdf).

The study repository lists `rna-seq.xlsx`, MANC v1.0 classifications/connectivity and FANC analysis notebooks. These are the concrete provenance inputs; snapshot/hash downloads and maintain the exact mapping trail to MaleCNS rather than treating names as interchangeable. [Data inventory](https://github.com/chrisjdallmann/feco-inhibition/blob/main/data/README.md), [Dryad dataset](https://doi.org/10.5061/dryad.gqnk98t16).

## Minimal implementation proposal (engineering inference)

1. Add an **axonal release state** to confidently mapped hook neurons, independent of their LIF membrane voltage and sensory drive. Keep existing measured connection counts unchanged.
2. Build a separate nonnegative matrix `A[j,i]` of measured counts for verified 9A-to-hook edges only. `i` is presynaptic 9A, `j` is the target hook axon. Remove those specific edges from the ordinary somatic-current pathway when this experimental mechanism is enabled, to avoid representing the same biological input twice. Do not remove any other GABA edges automatically.
3. From binary 9A spikes, update a low-pass activation state per hook axon. One bounded option is:

   ```text
   input_j = sum_i A[j,i] * spike_i / max(sum_i A[j,i], 1)
   a_j(t+dt) = exp(-dt/tau_gate) * a_j(t) + input_j
   release_j = 1 / (1 + beta * a_j)
   transmitted_spike_j = release_j * spike_j
   ```

   This is phenomenological release suppression. It is **not** a measured receptor occupancy equation, chloride model, or claim that suppressed calcium equals suppressed firing.
4. Apply `transmitted_spike` to outgoing synaptic transmission, while preserving the raw spike event for diagnostic plots. A downstream decoder should receive the state of downstream neurons, not a manually weakened actuator command. Report raw hook firing and release-weighted transmission separately.
5. Keep `tau_gate` and `beta` explicit, versioned calibration parameters. Start with a small predefined parameter grid, e.g. `tau_gate = 5, 20, 100 ms`, then vary `beta` over a logarithmic range; these are proposed numerical stress-test values, **not literature measurements**. Check convergence at smaller timesteps before interpreting timing.
6. Do not add hard-coded suppression whenever a UI label says “drawing.” Prefer recruitment through mapped circuit input. If a demonstration injects artificial 9A drive, expose it as experimental stimulation rather than a naturally generated motor command.

## Validation contract

### Numerical and causal tests

- Identical initial states and inputs must reproduce identical gate trajectories.
- With no 9A spikes, or `beta = 0`, release must recover to one. It must remain finite and within `[0,1]` under sustained high input.
- In a feed-forward isolated fixture, increasing 9A input should reduce hook transmission without directly changing the raw hook sensory spike generator.
- A virtual Rdl-block condition sets the hook gate to one while retaining its anatomical edges in the recorded graph. This is a **model intervention**, not a claim to reproduce a reported receptor knockout.
- Disable the verified 9A gate inputs separately from removing every inhibitory connection. This distinguishes the targeted hypothesis from generic disinhibition.
- Unmapped neurons and claw/club controls receive no direct gate modification. Recurrent indirect responses may still change; do not require every downstream neuron to remain numerically identical.
- Switching mechanism off must restore the declared baseline path exactly, including current routing and state reset policy.

### Empirical comparison, after identity mapping and dataset loading

Use matched passive kinematics and self-generated kinematics; compare hook versus claw/club. First evaluate stimulus replay, then active movement, then 9A stimulation and gate-block simulations. Report per-trial raw rates, transmitted rates, suppression ratio `(passive - active)/max(passive, epsilon)`, response recovery, and downstream motor error/contact. Treat these as our model metrics, not published target values.

For quantitative data fitting, use the repository's actual calcium observation model and train/test splits by animal. Fit the observation kernel/calibration on a training subset; assess held-out animals with correlations, amplitude errors and confidence intervals. Never compare an arbitrary normalized firing-rate trace directly with GCaMP amplitudes or optimize and score on the same trials. [Study figure-reproduction instructions and computational observation model](https://github.com/chrisjdallmann/feco-inhibition/blob/main/code/README.md).

## What this can establish

A successful first implementation can show that an explicitly mapped, receptor-supported **release-gating hypothesis** changes sensory transmission in the expected direction. It cannot establish measured synapse-specific conductance, receptor localization at every edge, full biological equivalence, or improved drawing until those outcomes are independently validated. Keep this experimental mechanism distinct from the working trained drawing controller until its motor readout has been recalibrated and tested.

## Implemented probe and mapping result

`research/prepare_receptor_probe.py` checks the pinned annotation, transmitter,
and connectivity hashes before extracting an isolated probe. The study's pinned
`manc_9A_web_connectivity.ipynb` explicitly identifies hook cells as `SNpp38` and
lists six chief 9A IDs. We match those chiefs by MANC ID **and** `IN09A012`, side,
and thoracic segment, avoiding a conflicting ID annotation on an unrelated cell.
The six hook homologs match `SNpp38` in both type fields; their segment remains
unresolved. This is a cross-specimen homology mapping, not direct receptor
measurement in MaleCNS.

The extraction finds **zero recorded chief 9A → hook edges** in the pinned
MaleCNS weights file. Eleven of the twelve candidate cells are absent from the
active 2,048-cell circuit. These facts do not prove that biological connections
are absent: classification, completeness, other 9A cells, and cross-dataset
correspondences need further investigation. They do prevent us from justifying
a release-gating connection in this graph. No edges are fabricated and no
production expansion is performed. Exact cells and counts are recorded in
`research/results/receptor-probe-manifest.json`.

`research/receptor_gate.py` implements a persistent experimental release state,
separate raw spikes and transmitted output, recovery, targeted input blockade,
a virtual receptor block, and explicit somatic routing to avoid double counting.
Its tests use **synthetic numerical fixtures**, not biological validation data.
The proposed tau, strength, and count normalization remain assumptions.

Reproduce the extraction and numerical checks:

```sh
# Superseded command: do not run prepare_receptor_probe.py; use audit_manc_receptors.py
.venv/bin/python -m unittest discover -s research -p 'test_receptor_gate.py'
```

The generated `research/data/receptor-probe.npz` is an ignored local artifact;
the extraction script and JSON manifest retain the reproducible record. The
working pencil controller and its checkpoint remain unchanged by this probe.

Next evidence needed: inspect broader 9A connectivity and the study's MANC/FANC
edge tables, resolve hook leg identity, then fit the release/observation model
with separate training and held-out animals. The public Dryad file-download API
returned HTTP 401 in this session, so no empirical calibration is claimed.

## Broader connectivity audit and recording preflight

The follow-up script `research/audit_receptor_connectivity.py` scans all **535**
MaleCNS cells whose type starts with `IN09A`, against the six matched `SNpp38`
cells. It finds one recorded synapse: `806152 (IN09A019) → 809853`, count 1.
This descriptive search does not establish that cell as a verified receptor
circuit member. It provides no basis for active-circuit expansion. See
`research/results/receptor-connectivity-audit.json` for the source hashes.

The Dryad website download link also returns HTTP 403 (the API download returns
401). Public metadata is accessible. File hashes, lengths and URLs are pinned in
`research/results/receptor-recording-sources.json` for the connectivity table,
passive hook recordings, active hook recordings, claw/club controls, and the
BDN2 intervention. No biological recordings have been fitted or scored.

Once these files are available under `work/receptor-study`, run:

```sh
.venv/bin/python research/prepare_receptor_recordings.py
```

The preflight verifies published hashes and required columns, rejects missing
inputs, and locks separate training, validation and test groups by animal ID
across files. It refuses to overwrite a changed split. Source-provided
`predicted_calcium` is excluded from fitting inputs because its provenance does
not guarantee an independently held-out prediction. Animal IDs must be reviewed
for consistency across datasets before interpreting results.

The authors' `imaging_predict_gcamp.m` uses a difference-of-exponentials calcium
observation kernel (30 ms rise, 300 ms decay). These are **calcium observation**
constants, not measured receptor-gating kinetics. Any receptor fit must model
transmission and observation separately. Active/passive labels alone cannot
establish that a modeled 9A circuit caused suppression. Numerical split tests
are infrastructure checks, not held-out biological validation.

## Recorded intervention check

`research/analyze_receptor_intervention.py` reproduces the study-style BDN2
stimulation-offset contrast with stimulated and subsequent control trials kept
separate. Across five animals, the mean paired calcium rebound difference is
1.836 in the published units; an exploratory animal bootstrap interval is
[1.055, 2.468]. This is a fixed contrast without fitted parameters and is not
a held-out receptor-model test. BDN2 stimulation is not Rdl-specific. Trial
contrasts, angle changes, source hash and method are recorded in
`research/results/receptor-intervention.json`.
