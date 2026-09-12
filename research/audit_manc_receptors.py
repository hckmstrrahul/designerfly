"""Version-aware MANC receptor audit and isolated measured MaleCNS probe.

No graph expansion or production motor changes. Requires the original study
download and the official MANC v1.0 neuron-properties feather file.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import numpy as np
import pyarrow as pa
import pyarrow.feather as feather
import pyarrow.parquet as parquet
from prepare_spiking import ANNOTATIONS_SHA256, checked_hash

ROOT = Path(__file__).resolve().parent.parent
MANC_URL = 'https://storage.googleapis.com/flyem-manc-exports/v1.0/manc-v1.0-neuron-properties.feather'
MANC_SHA256 = '0c4476528906bb0a20e05e1f01e83fc2e5a582761536171ede5463669ca0b891'
CONNECTIVITY_SHA256 = 'dddb20a6f3145ca801ad75a9b3aa9fe2db61ad87c78acd4b8cab0025d3556c0f'
CHIEFS = [(100513,'L','T1'),(13157,'L','T2'),(14517,'L','T3'),(165560,'R','T1'),(12443,'R','T2'),(12804,'R','T3')]

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def run(study, properties):
    checked_hash(properties, MANC_SHA256)
    recording_sources = json.loads((ROOT/'research/results/receptor-recording-sources.json').read_text())
    recorded = [r['sha256'] for r in recording_sources['files'] if r['name'] == 'manc_v1_connectivity.parquet']
    if recorded != [CONNECTIVITY_SHA256]:
        raise ValueError('Recorded study connectivity provenance changed')
    checked_hash(study/'manc_v1_connectivity.parquet', CONNECTIVITY_SHA256)
    checked_hash(ROOT/'research/data/annotations.feather', ANNOTATIONS_SHA256)
    manc = feather.read_table(properties).select(['bodyId','type','subclass','rootSide','instance']).to_pylist()
    ann = feather.read_table(ROOT/'research/data/annotations.feather').to_pylist()
    baseline = set(np.load(ROOT/'research/data/circuit-spiking.npz')['body_ids'].tolist())
    original = [r for r in manc if r['type'] == 'SNpp38']
    strict = [r for r in original if 'FeCO hook' in str(r['subclass'])]
    chiefs = []
    for body,side,segment in CHIEFS:
        matches = [r for r in ann if r['mancBodyid'] == body and r['type'] == 'IN09A012' and r['mancType'] == 'IN09A012' and r['somaSide'] == side and r['somaNeuromere'] == segment]
        if len(matches) != 1:
            raise ValueError(f'Ambiguous chief {body}')
        chiefs.extend(matches)
    hooks, mapping = [], []
    for source in strict:
        side = {'LHS':'L','RHS':'R'}.get(source['rootSide'])
        nerve = next((v for k,v in [('prothoracic','ProLN'),('mesothoracic','MesoLN'),('metathoracic','MetaLN')] if source['subclass'].startswith(k)), None)
        candidates = [r for r in ann if r['mancBodyid'] == source['bodyId']]
        valid = [r for r in candidates if side and nerve and r['rootSide'] == side and r['entryNerve'] == nerve and r['class'] == 'mechanosensory_proprioceptive']
        record = {'manc_body_id':source['bodyId'],'manc_v1_type':source['type'],'manc_v1_subclass':source['subclass'],'manc_side':side,'expected_nerve':nerve,'candidate_body_ids':[r['bodyId'] for r in candidates], 'accepted':len(valid)==1}
        if len(valid)==1:
            hooks.extend(valid)
            record.update({'male_cns_body_id':valid[0]['bodyId'],'male_cns_type':valid[0]['type'],'in_baseline':valid[0]['bodyId'] in baseline})
        else:
            record['reason'] = 'missing_or_ambiguous_side_nerve_class_validated_match'
        mapping.append(record)
    if len({r['bodyId'] for r in hooks}) != len(hooks):
        raise ValueError('Duplicate mapped hook body')
    t = parquet.read_table(study/'manc_v1_connectivity.parquet',columns=['Presynaptic_ID','Postsynaptic_ID','Excitatory x Connectivity'])
    src,dst,val = (t[k].to_numpy() for k in t.column_names)
    chief_ids=[r[0] for r in CHIEFS]
    def summary(targets):
        mask=np.isin(src,chief_ids)&np.isin(dst,targets)
        return {'edges':int(mask.sum()),'signed_weight_sum':float(val[mask].sum()),'absolute_weight_sum':float(np.abs(val[mask]).sum()),'negative_edges':int((val[mask]<0).sum()),'rows':[{'pre':int(a),'post':int(z),'signed_weight':float(w)} for a,z,w in zip(src[mask],dst[mask],val[mask])]}
    counts = np.zeros((len(hooks),len(chiefs)))
    pre={r['bodyId']:i for i,r in enumerate(chiefs)}
    post={r['bodyId']:i for i,r in enumerate(hooks)}
    weights=ROOT/'research/data/weights.feather'
    expected=json.loads((ROOT/'research/results/graph-manifest.json').read_text())['source_sha256']['weights.feather']
    checked_hash(weights,expected)
    with pa.memory_map(str(weights),'r') as stream:
        reader=pa.ipc.open_file(stream)
        for i in range(reader.num_record_batches):
            b=reader.get_batch(i)
            a,z=b['body_pre'].to_numpy(),b['body_post'].to_numpy()
            mask=np.isin(a,list(pre))&np.isin(z,list(post))
            for s,d,n in zip(a[mask],z[mask],b['weight'].to_numpy()[mask]):
                counts[post[int(d)],pre[int(s)]]+=n
    cells=[{'role':role,**{k:r[k] for k in ['bodyId','mancBodyid','type','rootSide','entryNerve','somaSide','somaNeuromere']},'in_baseline':r['bodyId'] in baseline} for role,rr in [('chief_9A',chiefs),('hook',hooks)] for r in rr]
    edges=[{'pre':chiefs[j]['bodyId'],'post':hooks[i]['bodyId'],'count':int(counts[i,j])} for i,j in zip(*np.nonzero(counts))]
    forechief=[j for j,r in enumerate(chiefs) if r['somaNeuromere']=='T1']
    forehook=[i for i,r in enumerate(hooks) if r['entryNerve']=='ProLN']
    old=[r for r in ann if r['type']=='SNpp38' and r['mancType']=='SNpp38']
    by_id={r['bodyId']:r for r in manc}
    old_mapping=[{'male_cns_body_id':r['bodyId'],'manc_body_id':int(r['mancBodyid']),'original_manc_v1_type':by_id[int(r['mancBodyid'])]['type'],'original_subclass':by_id[int(r['mancBodyid'])]['subclass']} for r in old]
    with (study/'manc_v1_classifications.csv').open() as stream:
        classifications=list(csv.DictReader(stream))
    report={'audit_date':'2026-09-13','production_changed':False,'study_doi':'10.1038/s41586-025-09554-2','data_doi':'10.5061/dryad.gqnk98t16','data_version':'20250903','original_manc_properties_url':MANC_URL,'notebook_url':'https://github.com/chrisjdallmann/feco-inhibition/blob/e1233f4a987c532c9f1ab42273af21a0a6a50393/code/manc_9A_web_connectivity.ipynb','sha256':{properties.name:sha(properties),'manc_v1_connectivity.parquet':sha(study/'manc_v1_connectivity.parquet'),'manc_v1_classifications.csv':sha(study/'manc_v1_classifications.csv'),'male_cns_annotations.feather':ANNOTATIONS_SHA256,'male_cns_weights.feather':expected},'classifications_columns':list(classifications[0]),'classifications_rows':len(classifications),'notebook_output_limit':'Saved outputs are the web-neuron example, not a saved list of hook IDs; source explicitly queries SNpp38 in manc:v1.0 and filters displayed edges at >=5 synapses. This audit retains every nonzero table row.','connectivity_semantics':'Presynaptic_ID -> Postsynaptic_ID; Excitatory x Connectivity is already signed and multiplied by global w_syn in the study model. It is not raw unsigned anatomy.','original_snpp38_neurons':len(original),'original_snpp38_subclasses':dict(Counter(r['subclass'] or 'missing' for r in original)),'strict_original_hook_neurons':len(strict),'accepted_hook_homologs':len(hooks),'mapping_rule':'Original MANC v1.0 type SNpp38 AND explicit FeCO hook subclass; then body crosswalk, matching root side, thoracic entry nerve and proprioceptive class, unique match required. Homology evidence is not direct receptor measurement in MaleCNS.','hook_mapping':mapping,'incorrect_previous_type_mapping':old_mapping,'manc_chief_outgoing_edges':int(np.isin(src,chief_ids).sum()),'manc_chief_to_original_snpp38':summary([r['bodyId'] for r in original]),'manc_chief_to_strict_hooks':summary([r['bodyId'] for r in strict]),'cells':cells,'male_cns_edges':edges,'male_cns_nonzero_edges':len(edges),'male_cns_synapse_sum':int(counts.sum()),'additional_cells':sum(not c['in_baseline'] for c in cells),'foreleg':{'chiefs':len(forechief),'hooks':len(forehook),'edges':int(np.count_nonzero(counts[np.ix_(forehook,forechief)])),'synapses':int(counts[np.ix_(forehook,forechief)].sum())},'conclusion':'Previous zero-edge result used cross-version type names and tested wing cells. Corrected original-ID mappings support an isolated measured connectivity probe; no motor promotion, receptor conductance claim or production graph expansion follows from this audit.'}
    (ROOT/'research/results/receptor-manc-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    np.savez_compressed(ROOT/'research/data/receptor-mapped-probe.npz',counts=counts,source_body_ids=list(pre),target_body_ids=list(post))
    print(json.dumps({k:report[k] for k in ['strict_original_hook_neurons','accepted_hook_homologs','male_cns_nonzero_edges','male_cns_synapse_sum','additional_cells','foreleg']}))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--study-dir',type=Path,required=True)
    p.add_argument('--manc-properties',type=Path,required=True)
    a=p.parse_args()
    run(a.study_dir,a.manc_properties)
