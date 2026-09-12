"""Verify biological inputs and lock animal-level splits; does not fit a model.

Source-published predicted_calcium is deliberately excluded: its fitting history
is not an independently held-out model evaluation. No synthetic fallback exists.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = {'animal_id','trial','time','calcium','L1C_flex'}

def animal_split(animals):
    unique = sorted(set(animals), key=lambda a:hashlib.sha256(('receptor-v1:'+a).encode()).hexdigest())
    if len(unique) < 4:
        raise ValueError('At least four animals required for separate fit, validation, and test sets')
    n = max(1,len(unique)//5)
    return {'test':unique[:n], 'validation':unique[n:2*n], 'train':unique[2*n:]}

def prepare(directory):
    spec = json.loads((ROOT/'research/results/receptor-recording-sources.json').read_text())
    missing = [f['name'] for f in spec['files'] if not (directory/f['name']).is_file()]
    if missing:
        raise ValueError('Missing biological files; no calibration performed: '+', '.join(missing))
    recordings=[]; animals=[]
    for f in spec['files']:
        path=directory/f['name']
        with path.open('rb') as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
        if digest != f['sha256']: raise ValueError('Source digest mismatch: '+f['name'])
        if f['name'].startswith('manc_'): continue
        schema=set(pq.read_schema(path).names)
        required = REQUIRED | ({'stimulus'} if f['name']=='hook_flexion_03_bdn2.parquet' else {'analyze'})
        if not required <= schema: raise ValueError(f"Missing columns in {f['name']}: {required-schema}")
        ids=pq.read_table(path,columns=['animal_id'])['animal_id'].to_pylist()
        if any(a is None for a in ids): raise ValueError('Null animal identifier')
        ids=sorted({str(int(a)) if isinstance(a,(int,float)) and float(a).is_integer() else str(a) for a in ids}); animals.extend(ids)
        recordings.append({'file':f['name'],'sha256':digest,'animals':ids,'score_mask':'analyze=1' if 'analyze' in schema else 'all finite observations; intervention file has no analyze flag'})
    report={'status':'inputs verified; calibration not yet performed','split':animal_split(animals),
            'recordings':recordings,'unit':'animal_id across files, conservatively shared when identifiers coincide',
            'protocol':'Fit only training animals; choose hyperparameters on validation animals; evaluate test once. Reset observation/gate state per trial, retain excluded frames for time evolution, score only analyze=1.',
            'limits':'This preflight does not establish receptor kinetics or validated motor improvement.'}
    destination=ROOT/'research/results/receptor-recording-split.json'
    if destination.exists() and json.loads(destination.read_text()) != report:
        raise ValueError('Locked split differs; review dataset version before replacing')
    destination.write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--data-dir',type=Path,default=ROOT/'work/receptor-study')
    args=parser.parse_args()
    try: print(json.dumps(prepare(args.data_dir),indent=2))
    except ValueError as error: parser.exit(2,str(error)+'\n')
