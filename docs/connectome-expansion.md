# Receptor evidence and expansion costs

Audit date: 2026-09-13. No active circuit, receptor effect or hosting plan changed.

The downloaded study data have now been checked: see the [corrected original-ID
connectivity audit](receptor-connectivity-followup.md) and [held-out biological
recording calibration](receptor-calibration.md). The previous same-name hook
mapping was invalid across dataset versions. No active controller change has
been justified by the calibration results.

## Biological effects

The selected MaleCNS circuit still uses predicted presynaptic transmitter signs,
not receptor-validated effects. The reviewed public data did not support a
confident receptor-specific override for any selected connection.

There is relevant evidence: [Dallmann et al. 2025](https://faculty.washington.edu/tuthill/docs/Dallmann_et_al-2025-Nature.pdf)
reports Rdl/GABA-A expression and presynaptic inhibition in leg proprioceptive
hook neurons. [Code and data](https://github.com/chrisjdallmann/feco-inhibition)
and [Dryad data](https://doi.org/10.5061/dryad.gqnk98t16) provide a concrete starting
point. However, the cited chief-9A neurons map to a type absent from our selection,
and the hook neurons require validated cross-dataset matching. Presynaptic shunting
and release suppression also need axonal dynamics; a negative somatic LIF weight
would not establish reproduction of that mechanism.

The next defensible extension is to match the documented cells using type, side,
anatomy and cross-dataset identifiers; add their measured circuit if required;
implement the receptor mechanism with explicitly calibrated parameters; and test
against the biological experiment before retraining the drawing readout. Unmatched
connections retain explicit uncertainty. A connectome or transcriptomic cluster
label alone does not verify every connection's physiological effect.

See `research/results/receptor-evidence-audit.json` for the reviewed evidence.

## Measured local sizing

`research/benchmark_connectome_cost.py` benchmarks the existing 2,048 and 4,096
cell graphs with the same sparse LIF implementation and predicted-sign rule. This
is a constant-drive circuit benchmark, not validation of a larger pencil controller.
Five one-second simulation trials follow a 200 ms warmup. No graph is installed.

| Graph | Cell-to-cell edges | Sparse weights + five state arrays per session | CPU seconds per simulated second |
|---|---:|---:|---:|
| 2,048 neurons | 192,267 | 2.29 MiB | 0.123 |
| 4,096 neurons | 534,990 | 6.29 MiB | 0.366 |

Doubling neurons increases measured neural CPU work about 3x because connectivity
also grows. Physics, the motor readout, HTTP, rendering and imports are excluded.
The local backend's import peak RSS was about 242 MiB; that is not a Railway
memory measurement. At 6x playback the neural work per wall second also increases
sixfold if the machine can keep up; additional users require their own dynamic
state and simulation work. Current code allocates separate sparse weights per
spiking session; sharing immutable matrices would reduce memory at larger sizes.

Raw results: `research/results/connectome-cost-benchmark.json`. These timings are
from a local Apple arm64 CPU, not Railway hardware.

## Hosting estimates

[Railway pricing](https://docs.railway.com/pricing/plans), checked on the audit date:
Hobby has a $5 monthly minimum including $5 usage; standard service CPU is
$20/vCPU-month, RAM $10/GB-month, and egress $0.05/GB. Resource billing depends on
actual usage. Illustrative 30-day resource budgets, excluding egress/storage:

| Average resources used | Approximate resource bill |
|---|---:|
| 0.5 GB RAM + 0.25 vCPU | $10/month |
| 1 GB RAM + 0.5 vCPU | $20/month |
| 2 GB RAM + 1 vCPU | $40/month |

These are resource scenarios, not promises for particular graph sizes or user
counts. The base subscription is credited toward usage, not added a second time.
If Railway CPU timing matched the local benchmark, one continuously active 1x
simulation would spend roughly $2.45/month on the 2k LIF core versus $7.31 on the
4k core, before other work. At 10% duty cycle those CPU components are one tenth.
Cloud hardware, request rate, playback speed and concurrency require live profiling.

Neural telemetry is also a scaling cost: the current API sends the whole activity
vector per update. Large circuits need sampled or aggregated visualization data.

A full male CNS has over 166,000 neurons and 125 million synaptic contacts
([primary project announcement](https://research.google/blog/a-connectomics-milestone-mapping-the-complete-male-fruit-fly-brain/)).
Synaptic contacts are not the same count as aggregated cell-to-cell edges.
Full-CNS operation would require a separate sparse/event-driven or accelerator
performance study, telemetry changes and motor validation before a credible cloud
budget can be quoted. It is not a simple service-size upgrade.

## Expected benefits

Expansion can retain more real pathways and support additional sensory or motor
experiments if their inputs, outputs and physiology are implemented. Extra cells
do not automatically create vision, memory, language or better pen control.

Our earlier single-seed rate-model comparison found essentially unchanged drawing
error: 0.011407 mean stroke RMSE at 2,048 versus 0.011423 at 4,096. The corresponding
training runs took 59 versus 227 seconds locally. These historical results are
not spiking-model benchmarks and do not prove expansion can never help.

For the drawing product, keep the validated 2k controller until a larger one
shows a measured benefit. For biological fidelity, a targeted receptor-supported
leg circuit is a more informative next experiment than simply maximizing cell count.
