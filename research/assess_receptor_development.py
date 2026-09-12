"""Record development rejection/readiness without reading sealed recordings.

A favorable development score still does not authorize runtime promotion.
"""
import hashlib
import json
from pathlib import Path
from receptor_acceptance import assess

ROOT=Path(__file__).resolve().parents[1]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    result=ROOT/'research/results/receptor-calibration-v3-development.json'
    contract_path=ROOT/'research/results/receptor-integration-v3-contract.json'
    r=json.loads(result.read_text());contract=json.loads(contract_path.read_text())
    candidate={a:v['all']['mse'] for a,v in r['outer_predictions']['tonic_candidate'].items()}
    control={a:v['all']['mse'] for a,v in r['outer_predictions'][r['strongest_control']].items()}
    score=assess(candidate,control,kind='primary',contract=contract)
    baseline=contract['candidate_isolation']['baseline_snapshot']
    unchanged={name:sha(ROOT/name)==expected for name,expected in baseline.items()}
    report={'scope':'Development comparison only; NOT a confirmatory biological or motor validation',
            'development_report_sha256':sha(result),'contract_sha256':sha(contract_path),
            'candidate':'tonic-release calcium surrogate','comparator':r['strongest_control'],
            'development_assessment':score,
            'decision':'eligible for consideration of sealed prediction test only' if score['passed'] else 'reject development candidate; preserve sealed cohorts',
            'fresh_confirmation_performed':False,'reserved_cohorts_read':False,
            'spike_to_observation_bridge_validated':False,
            'motor_training_started':False,'motor_contact_validation_started':False,
            'production_promotion':False,'baseline_unchanged':unchanged,
            'remaining':'A better development model and a consistent spike-to-observation bridge must precede fresh biological confirmation, then candidate motor-interface training and physical validation.'}
    if not all(unchanged.values()):raise ValueError('Validated baseline changed during research')
    output=ROOT/'research/results/receptor-refinement-decision.json'
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'decision':report['decision'],'baseline_unchanged':all(unchanged.values()),'motor_training_started':False}))

if __name__=='__main__':main()
