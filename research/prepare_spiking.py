"""Join official neuron-level predictions to the existing circuit; no fitted gains."""
import hashlib, json
from collections import Counter
from pathlib import Path
import numpy as np
import pyarrow.feather as feather

ROOT = Path(__file__).resolve().parent.parent
SOURCE = 'https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/body-neurotransmitters-male-cns-v1.0.feather'
ANNOTATIONS_SOURCE = 'https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/body-annotations-male-cns-v1.0-minconf-0.5.feather'
SOURCE_SHA256 = '95c9289220663abeb3409f3ad9e5a7f8a53f8093f5139d15502cd08da8879621'
GRAPH_SHA256 = '3b259bfd9b4878dd2133402c192680f08782d75c9af8861a1207da66c5b14e0f'
ANNOTATIONS_SHA256 = '2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2'
CONFIDENCE_THRESHOLD = .5
POLARITY = {'acetylcholine': 1, 'gaba': -1, 'glutamate': -1}

def checked_hash(path, expected):
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f'{path.name}: source changed; review provenance before rebuilding')
    return actual

def prediction(record):
    """Return the prediction and an auditable reason; never infer missing effects."""
    if record is None:
        return 'unknown', 0., 0, 'missing_record'
    label = record.get('predicted_nt') or 'unknown'
    raw = record.get('predicted_nt_confidence')
    if raw is None:
        return label, 0., 0, 'missing_confidence'
    score = float(raw)
    if not np.isfinite(score) or not 0 <= score <= 1:
        raise ValueError('Neurotransmitter confidence must be finite and within [0, 1]')
    if label == 'unknown':
        return label, score, 0, 'missing_label'
    if score < CONFIDENCE_THRESHOLD:
        return label, score, 0, 'low_confidence'
    if label not in POLARITY:
        return label, score, 0, 'unmodeled_transmitter'
    return label, score, POLARITY[label], 'assumed_fast_effect'

def prepare():
    source = ROOT/'research/data/neurotransmitters.feather'
    graph_path = ROOT/'research/data/circuit-2048.npz'
    annotations_path = ROOT/'research/data/annotations.feather'
    checked_hash(source, SOURCE_SHA256)
    checked_hash(graph_path, GRAPH_SHA256)
    checked_hash(annotations_path, ANNOTATIONS_SHA256)
    graph = np.load(graph_path)
    source_rows = feather.read_table(source).to_pylist()
    records = {r['body']: r for r in source_rows}
    if len(records) != len(source_rows):
        raise ValueError('Duplicate neurotransmitter body IDs')
    annotations = {r['bodyId']: r for r in feather.read_table(annotations_path).select(['bodyId', 'receptorType']).to_pylist()}
    labels, confidence, signs = [], [], []
    audit = []
    # Fast chemical effects only: receptor-specific effects and modulation are unresolved.
    for body in graph['body_ids']:
        label, score, sign, reason = prediction(records.get(int(body)))
        labels.append(label); confidence.append(score)
        signs.append(sign)
        audit.append([int(body), label, score, sign, reason])
    target = ROOT/'research/data/circuit-spiking.npz'
    np.savez_compressed(target, **{k: graph[k] for k in graph.files}, signs=np.array(signs,dtype=np.int8), nt=np.array(labels), confidence=np.array(confidence))
    report = {'source': SOURCE, 'license': 'CC-BY-4.0', 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'graph_sha256': hashlib.sha256(graph_path.read_bytes()).hexdigest(), 'neurons': len(signs), 'edges': len(graph['counts']), 'confidence_threshold': .5, 'excitatory': signs.count(1), 'inhibitory': signs.count(-1), 'unresolved': signs.count(0), 'weight_rule': '0.15 mV per measured synapse, multiplied by presynaptic assumed sign; no normalization or learned edge gains', 'assumptions': 'ACh excitatory; GABA and glutamate inhibitory in this central-circuit probe. Receptor-specific exceptions are not modeled. Low-confidence, missing and modulatory labels have zero fast transmission; edges remain in the anatomical graph.', 'scope': 'Signed LIF circuit for an offline-trained physical motor interface; predicted signs are not receptor-validated biology'}
    report.update({
        'dataset': 'male-cns:v1.0',
        'source_documentation': 'https://male-cns.janelia.org/download/',
        'annotations_source': ANNOTATIONS_SOURCE,
        'annotations_sha256': ANNOTATIONS_SHA256,
        'source_hashes_pinned': True,
        'prediction_field': 'predicted_nt (neuron-level aggregate; not consensus_nt or cell-type substitution)',
        'label_counts': dict(sorted(Counter(labels).items())),
        'effect_reason_counts': dict(sorted(Counter(row[4] for row in audit).items())),
        'receptor_audit': {
            'selected_annotation_records': sum(int(body) in annotations for body in graph['body_ids']),
            'selected_non_null_receptor_type': sum(annotations.get(int(body), {}).get('receptorType') is not None for body in graph['body_ids']),
            'available_non_null_values': sorted({r['receptorType'] for r in annotations.values() if r['receptorType']}),
            'interpretation': 'Available receptorType values are putative sensory receptor labels on gustatory neurons, not a postsynaptic neurotransmitter-receptor expression matrix. No receptor-specific connection signs can be inferred for this selected graph.',
            'resolved_connection_effects': 0,
        },
        'limitations': ['Transmitter predictions and confidence are not experimentally verified polarity.', 'Presynaptic sign is a modeling assumption; postsynaptic receptor-specific exceptions and co-transmission are unresolved.', 'Glutamate is assumed inhibitory for central connections; this does not describe excitatory glutamatergic neuromuscular junctions.', 'Synapse counts are anatomical measurements, not measured electrophysiological conductances. Global gain and membrane constants are model parameters.'],
        'neuron_audit_columns': ['body_id', 'predicted_nt', 'confidence', 'assumed_sign', 'reason'],
    })
    # One compact row per neuron keeps IDs, original confidence and exclusions reviewable.
    manifest = json.dumps(report, indent=2)[:-2] + ',\n  "neuron_audit": [\n'
    manifest += ',\n'.join('    ' + json.dumps(row) for row in audit) + '\n  ]\n}\n'
    (ROOT/'research/results/spiking-manifest.json').write_text(manifest)
    print(json.dumps(report,indent=2))

if __name__ == '__main__': prepare()
