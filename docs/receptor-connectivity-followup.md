# Correcting the hook-neuron identity audit

2026-09-13. The previous zero-edge finding does **not** establish that the expected receptor circuit is absent. It queried the wrong population by reusing a cell-type name across dataset versions.

The study notebook explicitly queries `SNpp38` in `manc:v1.0`. The official MANC v1.0 properties table contains 108 such cells. Current MaleCNS annotations contain only six cells named `SNpp38`; their MANC body matches are **SNpp05 wing proprioceptors in the original v1.0 dataset**. These six cells cannot stand in for the study's leg-hook population. [Version-pinned notebook](https://github.com/chrisjdallmann/feco-inhibition/blob/e1233f4a987c532c9f1ab42273af21a0a6a50393/code/manc_9A_web_connectivity.ipynb), [official original properties](https://storage.googleapis.com/flyem-manc-exports/v1.0/manc-v1.0-neuron-properties.feather).

The original 108-cell class is itself heterogeneous in annotations: 56 explicit FeCO hook cells, 14 club, one claw, and 37 without a specific hook label. The corrected audit conservatively starts with the 56 explicitly annotated hooks. It maps original body IDs to MaleCNS only when side, thoracic entry nerve and proprioceptive class also agree, and requires a unique surviving match. This yields 35 candidate homologs. Their current names need not equal the original name. This remains cross-specimen anatomical evidence, not a direct receptor assay in MaleCNS.

| Check | Result |
|---|---:|
| Six original chief-9A cells: all outgoing study-table rows | 166 |
| Chief to original MANC `SNpp38` | 71 negative-weight edges, absolute weight sum 4,021 |
| Chief to explicit original hook subclass | 45 negative-weight edges, absolute weight sum 3,304 |
| Corrected MaleCNS chief-to-hook candidate connections | 35 edges, 2,724 measured synapses |
| Foreleg subset | Two chiefs, five hook homologs, five edges, 155 measured synapses |
| Candidate cells absent from the active graph | All 41: six chiefs and 35 hook homologs |

The study's parquet columns are directional: `Presynaptic_ID` to `Postsynaptic_ID`. `Excitatory x Connectivity` is an already signed model weight. The study multiplies it by its global `w_syn`; it should not be relabeled as raw anatomical counts. By contrast, the corrected MaleCNS probe uses unsigned measured `weight` from the local full connection table. No threshold is applied to our audit's nonzero rows; the study notebook thresholds displayed connections at five synapses. Its saved outputs show the web-neuron example, not a frozen hook-ID result table. [Study model implementation](https://github.com/chrisjdallmann/feco-inhibition/blob/e1233f4a987c532c9f1ab42273af21a0a6a50393/code/simulation_model.py).

## Reproduction

Download the original properties file linked above, then run:

```sh
.venv/bin/python research/audit_manc_receptors.py \
  --study-dir /Users/rahulc/Downloads/doi_10_5061_dryad_gqnk98t16__v20250903 \
  --manc-properties work/receptor-study/manc-v1.0-neuron-properties.feather
```

The script checks pinned hashes for the original properties, study connectivity, MaleCNS annotations and full MaleCNS weights. It also checks study connectivity provenance against `receptor-recording-sources.json`. Outputs are `research/results/receptor-manc-audit.json` (every accepted/rejected mapping and relevant edges) and `research/data/receptor-mapped-probe.npz` (counts indexed target by source). It does not modify the production graph or motor.

## Expansion decision

The correction supports a small **experimental** circuit: the foreleg subset would require seven additional cells. It does not justify adding every neuron from the original broad class or promoting a receptor gate to the drawing motor. Some original hook identities remain unmatched or ambiguous, and receptor expression is population-level evidence. Gate parameters have not been validated in this spike model; behavioral calcium calibration alone cannot be transferred directly to axonal release dynamics. The next meaningful step is validation of this mapped probe, followed by motor recalibration only if its physiological behavior is supported.

The earlier `receptor-probe-manifest.json` and `receptor-connectivity-audit.json` represent superseded cross-version selections. Their zero/near-zero connectivity results must not be cited as evidence against the corrected circuit.
