"""Reproduce a paired BDN2 stimulus-offset contrast; no receptor fitting.

The authors align even stimulation trials and subsequent odd control trials to
stimulation offset, then compare late-window to early post-offset calcium.
This implementation keeps the two conditions separate and reports animal means.
BDN2 stimulation is not an Rdl-specific perturbation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parent.parent
SOURCE='https://github.com/chrisjdallmann/feco-inhibition/blob/e1233f4a987c532c9f1ab42273af21a0a6a50393/code/imaging_BDN2_activation.ipynb'

def analyze(directory):
    name='hook_flexion_03_bdn2.parquet'; path=directory/name
    manifest=json.loads((ROOT/'research/results/receptor-recording-sources.json').read_text())
    expected=next(f['sha256'] for f in manifest['files'] if f['name']==name)
    with path.open('rb') as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
    if digest!=expected: raise ValueError('Biological input hash mismatch')
    table=pq.read_table(path); data={k:table[k].to_numpy() for k in table.column_names}
    per_animal=[]
    for animal in np.unique(data['animal_id']):
        pairs=[]
        for trial in [2,4,6,8,10]:
            stim_idx=np.flatnonzero((data['animal_id']==animal)&(data['trial']==trial))
            control_idx=np.flatnonzero((data['animal_id']==animal)&(data['trial']==trial+1))
            stim_idx=stim_idx[np.argsort(data['time'][stim_idx])]; control_idx=control_idx[np.argsort(data['time'][control_idx])]
            offsets=np.flatnonzero(np.diff(data['stimulus'][stim_idx])<0)
            if len(offsets)!=1: raise ValueError('Expected exactly one stimulus offset')
            # Authors use 8.01 Hz, 3 s window with 1 s pre-offset.
            begin=int(offsets[0])-round(8.01)
            early=begin+round(8.01)+1
            late=begin+round(3*8.01)-1
            if begin<0 or late>=min(len(stim_idx),len(control_idx)): raise ValueError('Incomplete paired window')
            def change(indices,key):
                return float(data[key][indices[late]]-data[key][indices[early]])
            values={'stimulus_trial':trial,'control_trial':trial+1,
                    'stimulated_delta_calcium':change(stim_idx,'calcium'),
                    'control_delta_calcium':change(control_idx,'calcium'),
                    'stimulated_delta_angle':change(stim_idx,'L1C_flex'),
                    'control_delta_angle':change(control_idx,'L1C_flex')}
            if not all(np.isfinite(v) for v in values.values()): raise ValueError('Nonfinite contrast')
            pairs.append(values)
        stim=np.mean([p['stimulated_delta_calcium'] for p in pairs]);control=np.mean([p['control_delta_calcium'] for p in pairs])
        per_animal.append({'animal':int(animal),'stimulated_delta_calcium':float(stim),'control_delta_calcium':float(control),'paired_difference':float(stim-control),'pairs':pairs})
    differences=np.array([r['paired_difference'] for r in per_animal])
    rng=np.random.default_rng(20250903)
    bootstrap=rng.choice(differences,size=(10000,len(differences)),replace=True).mean(axis=1)
    report={'analysis':'fixed study-style BDN2 offset contrast; no fitted parameters', 'source':SOURCE,'input_sha256':digest,
            'animals':per_animal,'mean_paired_difference':float(differences.mean()),'animal_bootstrap_95_percent_interval':np.quantile(bootstrap,[.025,.975]).tolist(),
            'unit':'published calcium units; no cross-animal rescaling',
            'limitations':['Five animals; bootstrap uncertainty is exploratory.','BDN2 stimulation is not an Rdl-specific intervention.','This validates neither MaleCNS cell matching nor a learned motor policy.','Study-style offset rebound contrast, not receptor inhibition strength or kinetic estimate.'],
            'production_change':False}
    (ROOT/'research/results/receptor-intervention.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['mean_paired_difference','animal_bootstrap_95_percent_interval']}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--data-dir',type=Path,required=True)
    analyze(parser.parse_args().data_dir)
