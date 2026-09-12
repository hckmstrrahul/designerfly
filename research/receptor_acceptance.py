"""Evaluate preregistered animal-level prediction criteria, never enable runtime."""
import json
from pathlib import Path
import numpy as np

CONTRACT=Path(__file__).resolve().parent/'results/receptor-integration-contract.json'

def paired_metrics(candidate, baseline, contract):
    if set(candidate)!=set(baseline) or not candidate:
        raise ValueError('Exactly matched nonempty animal sets are required')
    animals=sorted(candidate)
    c=np.array([candidate[a] for a in animals],dtype=float)
    b=np.array([baseline[a] for a in animals],dtype=float)
    if not np.isfinite(c).all() or not np.isfinite(b).all() or np.any(c<0) or np.any(b<0):
        raise ValueError('MSE must be finite and nonnegative')
    epsilon=contract['metrics']['denominator_epsilon']
    if b.mean()<=epsilon:
        return {'status':'inconclusive','reason':'near-zero baseline MSE','animals':animals}
    uncertainty=contract['metrics']['uncertainty']
    rng=np.random.default_rng(uncertainty['seed'])
    indices=rng.integers(0,len(animals),size=(uncertainty['replicates'],len(animals)))
    denominators=b[indices].mean(axis=1)
    if np.any(denominators<=epsilon):
        return {'status':'inconclusive','reason':'near-zero bootstrap denominator','animals':animals}
    boot=1-c[indices].mean(axis=1)/denominators
    ci=np.quantile(boot,[.025,.975])
    return {'status':'evaluated','animals':animals,'n_animals':len(animals),
            'candidate_mse':float(c.mean()),'baseline_mse':float(b.mean()),
            'relative_improvement':float(1-c.mean()/b.mean()),
            'relative_improvement_ci95':ci.tolist(),
            'relative_regression_ci95':[-float(ci[1]),-float(ci[0])],
            'fraction_improved':float(np.mean(c<b)),
            'maximum_individual_regression':float(np.max((c-b)/np.maximum(b,epsilon)))}

def assess(candidate,baseline,*,kind,constant=None,contract=None):
    contract=contract or json.loads(CONTRACT.read_text())
    if kind not in {'primary','passive'}:raise ValueError('Unknown cohort role')
    report=paired_metrics(candidate,baseline,contract)
    if report['status']!='evaluated':return {**report,'passed':False}
    limits=contract['biological_acceptance'][kind]
    checks={'enough_animals':report['n_animals']>=contract['confirmatory_data']['minimum_independent_animals_per_cohort'],
            'individual_regression':report['maximum_individual_regression']<=limits['maximum_individual_relative_mse_regression']}
    if kind=='primary':
        checks.update({'mean_improvement':report['relative_improvement']>=limits['minimum_relative_mse_improvement'],
                       'uncertainty':report['relative_improvement_ci95'][0]>limits['relative_improvement_ci95_lower_strictly_greater_than'],
                       'fraction_improved':report['fraction_improved']>=limits['minimum_fraction_animals_with_strict_mse_improvement']})
    else:
        checks['noninferiority']=report['relative_regression_ci95'][1]<=limits['maximum_relative_mse_regression_ci95_upper']
        if constant is None:raise ValueError('Passive constant comparator is required')
        versus_constant=paired_metrics(candidate,constant,contract)
        report['versus_constant']=versus_constant
        checks['useful_prediction']=versus_constant['status']=='evaluated' and versus_constant['relative_improvement']>limits['minimum_relative_mse_improvement_vs_constant_strictly_greater_than']
    return {**report,'checks':checks,'passed':all(checks.values()),
            'scope':'Prediction criterion only; does not establish the spike bridge or motor readiness.'}
