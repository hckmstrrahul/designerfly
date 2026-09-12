"""Lock v2 cohorts using source checksums and identifier columns only.

Never read calcium or behavioral outcomes in reserved files. Development files
include all former test animals; v1 test results are already exposed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def lock(directory):
    spec=json.loads((ROOT/'research/results/receptor-v2-sources.json').read_text())
    expected={r['file']:r['sha256'] for r in spec['files']}
    roles={
        'hook_flexion_01_treadmill_platform.parquet':'development_active',
        'hook_flexion_01_magnet.parquet':'development_passive',
        '9A_treadmill_platform.parquet':'development_9a_observation',
        'hook_flexion_02_treadmill.parquet':'reserved_active',
        'hook_flexion_01_magnet_Mamiya2018.parquet':'reserved_passive',
    }
    files=[]
    for name,role in roles.items():
        path=directory/name; actual=digest(path)
        if actual!=expected[name]:raise ValueError('Source changed: '+name)
        ids=sorted({int(x) for x in pq.read_table(path,columns=['animal_id'])['animal_id'].to_pylist()})
        selected=[x for x in ids if x!=1] if role=='reserved_passive' else ids
        files.append({'file':name,'role':role,'sha256':actual,'animals':selected,
                      'excluded_animals':[1] if role=='reserved_passive' else []})
    report={'version':2,'data_doi':'10.5061/dryad.gqnk98t16','files':files,
            'reserved_outcomes_read':False,
            'exposure_note':'Only metadata/identity columns read for hook02. Two Mamiya animal1 outcome rows were viewed earlier; exclude animal1 from reserved passive evaluation. All hook01 and 9A development data may be used for training/cross-validation.',
            'identity_note':'hook02 uses JR252 versus hook01 R21D12; numerical IDs do not imply identical animals across driver cohorts. Treat all ROIs/trials within each cohort animal together. Mamiya2018 is a distinct historical cohort.',
            'test_rule':'Freeze all choices and verify protocol+model hashes before reading reserved outcomes; failed final test cannot be retuned and relabeled fresh.'}
    out=ROOT/'research/results/receptor-v2-data-plan.json'
    if out.exists() and json.loads(out.read_text())!=report:raise ValueError('Existing data lock differs; do not silently replace')
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'locked':str(out),'reserved_animals':{r['role']:len(r['animals']) for r in files if r['role'].startswith('reserved')}}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-dir',type=Path,required=True)
    lock(p.parse_args().data_dir)
