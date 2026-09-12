"""Passive-first development calibration. Reserved final recordings are never read."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from calibrate_receptor_recordings import load_segments, lowpass, sha

ROOT=Path(__file__).resolve().parents[1]
FILES={'passive':'hook_flexion_01_magnet.parquet','active':'hook_flexion_01_treadmill_platform.parquet','drive':'9A_treadmill_platform.parquet'}
RESPONSES=(('binary',20.),('binary',100.),('saturating',50.),('saturating',200.))
DECAYS=(.15,.30,.60)
GATE_TAUS=(.03,.10,.30,1.)
BETAS=(0.,.5,2.,8.)
SEED=20260913


def response(velocity,kind,scale):
    if kind=='binary':return (velocity < -scale).astype(float)
    if kind=='saturating':
        flexion=np.maximum(-velocity,0)
        return flexion/(scale+flexion)
    raise ValueError('Unknown response')


def observe(signal,dt,decay):
    return lowpass(lowpass(signal,dt,.03),dt,decay)


def predict_feature(segment,config,drive_only=False):
    drive=lowpass(segment['move'],segment['dt'],config.get('gate_tau',.1))
    if drive_only:return observe(drive,segment['dt'],.30)
    activation=response(segment['velocity'],config['kind'],config['scale'])
    release=1/(1+config.get('beta',0.)*drive)
    return observe(activation*release,segment['dt'],config['decay'])


def collect_stats(segments,config,drive_only=False):
    # n, sum x, sum y, sum xx, sum xy, sum yy: enough for affine fitting and MSE.
    out={}
    for s in segments:
        x=predict_feature(s,config,drive_only);y=s['y']
        for condition in ('all','active','not_actively_moving'):
            mask=s['score'].copy()
            if condition=='active':mask &= s['move']>.5
            if condition=='not_actively_moving':mask &= s['move']<=.5
            if not mask.any():continue
            xx=x[mask];yy=y[mask]
            out.setdefault(s['animal'],{}).setdefault(condition,np.zeros(6))[:] += [len(xx),xx.sum(),yy.sum(),xx@xx,xx@yy,yy@yy]
    return out


def fit(stats,animals,constant=False):
    selected=[stats[a]['all'] for a in animals if a in stats]
    if not selected:raise ValueError('No training animals')
    normalized=np.mean([s/s[0] for s in selected],axis=0)
    _,x,y,xx,xy,_=normalized
    if constant:return (0.,float(y))
    amplitude,offset=np.linalg.lstsq([[xx,x],[x,1]],[xy,y],rcond=None)[0]
    if amplitude<0:return (0.,float(y))
    return float(amplitude),float(offset)


def metrics(values,head):
    n,sx,sy,sxx,sxy,syy=values;a,b=head
    mse=max(0.,float((a*a*sxx+2*a*b*sx+b*b*n-2*a*sxy-2*b*sy+syy)/n))
    covariance=a*(sxy-sx*sy/n);vx=a*a*(sxx-sx*sx/n);vy=syy-sy*sy/n
    return {'frames':int(n),'mse':mse,'rmse':float(np.sqrt(mse)),
            'pearson_r':float(np.clip(covariance/np.sqrt(vx*vy),-1,1)) if a!=0 and vx>1e-9 and vy>1e-9 else None,
            'r2_against_animal_mean':float(1-mse*n/vy) if vy>1e-9 else None}


def evaluate(stats,animals,head):
    return {animal:{condition:metrics(values,head) for condition,values in stats[animal].items() if values[0]>=30} for animal in animals if animal in stats}


def mean_mse(rows):return float(np.mean([r['all']['mse'] for r in rows.values()]))


def select(candidates,animals):
    """Inner LOSO; each held-out animal contributes one error, not its frame count."""
    records=[]
    for config,stats in candidates:
        eligible=sorted(set(animals)&set(stats))
        if len(eligible)<2:raise ValueError('Need two inner training animals')
        errors=[]
        for animal in eligible:
            head=fit(stats,[a for a in eligible if a!=animal])
            errors.append(metrics(stats[animal]['all'],head)['mse'])
        records.append({'config':config,'inner_cv_mse':float(np.mean(errors)),'animals':eligible})
    best=min(range(len(records)),key=lambda i:records[i]['inner_cv_mse'])
    config,stats=candidates[best]
    return config,stats,fit(stats,animals),records


def paired_interval(candidate,control,seed=SEED):
    animals=sorted(set(candidate)&set(control));delta=np.array([control[a]['all']['mse']-candidate[a]['all']['mse'] for a in animals])
    draws=np.random.default_rng(seed).choice(delta,(10000,len(delta)),replace=True).mean(1)
    return {'animals':animals,'mean_mse_improvement':float(delta.mean()),'improvement_95_interval':np.quantile(draws,[.025,.975]).tolist(),
            'fraction_animals_improved':float(np.mean(delta>0)),'scope':'Development outer-fold predictions; not fresh confirmation'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'research/results/receptor-calibration-v2-development.json')
    parser.add_argument('--protocol',type=Path,default=ROOT/'docs/receptor-calibration-v2.md')
    args=parser.parse_args()
    animals=[str(i) for i in range(1,17)]
    shuffled=np.random.default_rng(SEED).permutation(animals)
    folds=[sorted(x.tolist(),key=int) for x in np.array_split(shuffled,3)]
    locked={'scope':'Development only; previously exposed hook01 data; no hook02 or Mamiya reads',
            'seed':SEED,'outer_folds':folds,'source_sha256':{name:sha(args.data_dir/file) for name,file in FILES.items()},
            'source_files':FILES,'helper_code_sha256':sha(ROOT/'research/calibrate_receptor_recordings.py'),'contract_sha256':sha(ROOT/'research/results/receptor-integration-contract.json'),'protocol_sha256':sha(args.protocol),'source_code_sha256':sha(__file__),
            'grids':{'responses':RESPONSES,'calcium_decay_seconds':DECAYS,'drive_tau_seconds':GATE_TAUS,'suppression_beta':BETAS}}
    lock_path=args.output.with_name(args.output.stem+'-preregistration.json')
    lock_path.write_text(json.dumps(locked,indent=2)+'\n')
    # Only the three explicitly named development files can be loaded here.
    segments={};quality={}
    for name,file in FILES.items():
        segments[name],quality[name]=load_segments(args.data_dir/file,{'development':animals},passive=name=='passive')
    passive_candidates=[]
    for kind,scale in RESPONSES:
        for decay in DECAYS:
            c={'kind':kind,'scale':scale,'decay':decay,'beta':0.,'gate_tau':.1}
            passive_candidates.append((c,collect_stats(segments['passive'],c)))
    drive_candidates=[]
    for tau in GATE_TAUS:
        c={'gate_tau':tau};drive_candidates.append((c,collect_stats(segments['drive'],c,True)))
    v1=[]
    for scale in (20.,50.,100.):
        for tau in (.03,.30):
            for beta in (0.,2.,10.):
                c={'kind':'binary','scale':scale,'decay':.30,'gate_tau':tau,'beta':beta}
                v1.append((c,collect_stats(segments['active'],c)))
    active_cache={}
    def active_stats(c):
        key=json.dumps(c,sort_keys=True)
        if key not in active_cache:active_cache[key]=collect_stats(segments['active'],c)
        return active_cache[key]
    def calibrate(train):
        passive_c,passive_s,passive_head,passive_cv=select(passive_candidates,train)
        drive_c,drive_s,drive_head,drive_cv=select(drive_candidates,train)
        gated=[({**passive_c,**drive_c,'beta':beta},active_stats({**passive_c,**drive_c,'beta':beta})) for beta in BETAS]
        gate_c,gate_s,gate_head,gate_cv=select(gated,train)
        nongated_c={**passive_c,**drive_c,'beta':0.};nongated_s=active_stats(nongated_c)
        v1_c,v1_s,v1_head,v1_cv=select(v1,train)
        fixed_c,fixed_s,fixed_head,fixed_cv=select([(c,s) for c,s in passive_candidates if c['decay']==.30],train)
        models={'candidate':(gate_c,gate_s,gate_head),'nongated':(nongated_c,nongated_s,fit(nongated_s,train)),
                'constant':({'constant':True},nongated_s,fit(nongated_s,train,True)), 'v1':(v1_c,v1_s,v1_head)}
        passive_models={'candidate':(passive_c,passive_s,passive_head),'fixed_kernel':(fixed_c,fixed_s,fixed_head),'constant':({'constant':True},passive_s,fit(passive_s,train,True))}
        metadata={'passive':{'config':passive_c,'head':passive_head,'cv':passive_cv},
                  'drive':{'config':drive_c,'head':drive_head,'cv':drive_cv},'suppression':{'cv':gate_cv},'v1':{'cv':v1_cv},'fixed_passive':{'cv':fixed_cv}}
        return models,passive_models,(drive_s,drive_head),metadata
    predictions={m:{} for m in ('candidate','nongated','constant','v1')}
    passive_predictions={m:{} for m in ('candidate','fixed_kernel','constant')}
    drive_predictions={'candidate':{},'constant':{}};fold_results=[]
    for i,heldout in enumerate(folds):
        train=[a for a in animals if a not in heldout]
        models,passive_models,(ds,dh),metadata=calibrate(train)
        for name,(_,stats,head) in models.items():predictions[name].update(evaluate(stats,heldout,head))
        for name,(_,stats,head) in passive_models.items():passive_predictions[name].update(evaluate(stats,heldout,head))
        drive_predictions['candidate'].update(evaluate(ds,heldout,dh));drive_predictions['constant'].update(evaluate(ds,heldout,fit(ds,train,True)))
        fold_results.append({'heldout':heldout,'calibration':metadata})
        print('Outer fold',i+1,{name:mean_mse(evaluate(stats,heldout,head)) for name,(_,stats,head) in models.items()},flush=True)
    chosen_control=min(('nongated','constant','v1'),key=lambda name:mean_mse(predictions[name]))
    final_models,final_passive,_,final_metadata=calibrate(animals)
    def frozen(models):return {name:{'config':c,'amplitude':h[0],'offset':h[1]} for name,(c,_,h) in models.items()}
    report={**locked,'quality':quality,'fold_results':fold_results,'outer_predictions':predictions,'passive_outer_predictions':passive_predictions,
            'drive_outer_predictions':drive_predictions,'active_mse':{m:mean_mse(r) for m,r in predictions.items()},
            'passive_mse':{m:mean_mse(r) for m,r in passive_predictions.items()},'drive_mse':{m:mean_mse(r) for m,r in drive_predictions.items()},
            'chosen_active_control':chosen_control,'candidate_vs_control':paired_interval(predictions['candidate'],predictions[chosen_control]),
            'frozen_active_models':frozen(final_models),'frozen_passive_models':frozen(final_passive),'final_calibration':final_metadata,
            'production_promotion':False,'reserved_tests_read':False,
            'limits':['Calcium-level behavioral proxy does not identify 9A spikes or receptor kinetics.','Observation heads differ because passive and active acquisition differ; no held-out calibration allowed.','All outer outcomes are development data; no fresh-test claim.','Final reserved cohorts require parent authorization after configuration freeze.']}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('active_mse','passive_mse','drive_mse','chosen_active_control','candidate_vs_control','frozen_active_models')},indent=2))

if __name__=='__main__':main()
