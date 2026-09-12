"""One bounded DEVELOPMENT revision: optional suppressible tonic calcium component."""
import argparse,json
from pathlib import Path
import numpy as np
from calibrate_receptor_recordings import load_segments,lowpass,sha
from calibrate_receptor_v2 import ROOT,FILES,observe,response,mean_mse,paired_interval

BETAS=(.5,2.,8.)


def collect(segments,c):
    output={}
    for s in segments:
        release=1/(1+c['beta']*lowpass(s['move'],s['dt'],c['gate_tau']))
        x=np.column_stack([observe(response(s['velocity'],c['kind'],c['scale'])*release,s['dt'],c['decay']),observe(release,s['dt'],c['decay'])])
        for condition in ('all','active','not_actively_moving'):
            mask=s['score'].copy()
            if condition=='active':mask &= s['move']>.5
            if condition=='not_actively_moving':mask &= s['move']<=.5
            if not mask.any():continue
            xx=x[mask];yy=s['y'][mask]
            output.setdefault(s['animal'],{}).setdefault(condition,np.zeros(11))[:] += np.r_[len(yy),xx.sum(0),yy.sum(),(xx.T@xx).ravel(),xx.T@yy,yy@yy]
    return output


def unpack(v):
    return v[0],v[1:3],v[3],v[4:8].reshape(2,2),v[8:10],v[10]


def fit(stats,animals,movement_only=False):
    rows=[stats[a]['all'] for a in animals if a in stats]
    if not rows:raise ValueError('No training animals')
    _,mx,my,xx,xy,_=unpack(np.mean([r/r[0] for r in rows],axis=0))
    covariance=xx-np.outer(mx,mx);target=xy-mx*my
    candidates=[np.zeros(2)]
    active_sets=[(1,)] if movement_only else [(0,),(1,),(0,1)]
    for active in active_sets:
        idx=list(active);solution=np.linalg.lstsq(covariance[np.ix_(idx,idx)],target[idx],rcond=None)[0]
        if np.all(solution>=-1e-10):
            coefficient=np.zeros(2);coefficient[idx]=np.maximum(solution,0);candidates.append(coefficient)
    coefficient=min(candidates,key=lambda a:float(a@covariance@a-2*a@target))
    return coefficient,float(my-coefficient@mx)


def metrics(v,head):
    n,sx,sy,xx,xy,yy=unpack(v);a,b=head
    mse=max(0.,float((a@xx@a+2*b*(a@sx)+b*b*n-2*a@xy-2*b*sy+yy)/n))
    variance_p=float(a@(xx-np.outer(sx,sx)/n)@a);variance_y=yy-sy*sy/n
    covariance=float(a@(xy-sx*sy/n))
    return {'frames':int(n),'mse':mse,'rmse':float(np.sqrt(mse)),
            'pearson_r':float(np.clip(covariance/np.sqrt(variance_p*variance_y),-1,1)) if variance_p>1e-9 and variance_y>1e-9 else None,
            'r2_against_animal_mean':float(1-mse*n/variance_y) if variance_y>1e-9 else None}


def evaluate(stats,animals,head):
    return {a:{condition:metrics(v,head) for condition,v in stats[a].items() if v[0]>=30} for a in animals if a in stats}


def select(candidates,animals,movement_only=False):
    scores=[]
    for c,s in candidates:
        eligible=sorted(set(animals)&set(s));errors=[]
        if len(eligible)<2:raise ValueError('Need at least two training animals')
        for a in eligible:errors.append(metrics(s[a]['all'],fit(s,[x for x in eligible if x!=a],movement_only))['mse'])
        scores.append({'config':c,'inner_cv_mse':float(np.mean(errors))})
    winner=min(range(len(scores)),key=lambda i:scores[i]['inner_cv_mse'])
    c,s=candidates[winner]
    return c,s,fit(s,animals,movement_only),scores


def packed(c,head):return {'config':c,'phasic_amplitude':float(head[0][0]),'tonic_amplitude':float(head[0][1]),'offset':head[1]}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-dir',type=Path,required=True)
    p.add_argument('--v2',type=Path,default=ROOT/'research/results/receptor-calibration-v2-development.json')
    p.add_argument('--output',type=Path,default=ROOT/'research/results/receptor-calibration-v3-development.json')
    args=p.parse_args();v2=json.loads(args.v2.read_text())
    for path,key in [(ROOT/'research/calibrate_receptor_v2.py','source_code_sha256'),(ROOT/'research/calibrate_receptor_recordings.py','helper_code_sha256'),(ROOT/'docs/receptor-calibration-v2.md','protocol_sha256'),(ROOT/'research/results/receptor-integration-contract-v2-snapshot.json','contract_sha256')]:
        if sha(path)!=v2[key]:raise ValueError('V2 provenance changed: '+str(path))
    for cohort,source_file in FILES.items():
        if sha(args.data_dir/source_file)!=v2['source_sha256'][cohort]:raise ValueError('V2 development source changed: '+source_file)
    file=FILES['active']
    if sha(args.data_dir/file)!=v2['source_sha256']['active']:raise ValueError('Development source changed')
    lock={'scope':'Development only; bounded tonic-release revision','v2_sha256':sha(args.v2),'source_sha256':v2['source_sha256'],
          'contract_sha256':sha(ROOT/'research/results/receptor-integration-v3-contract.json'),'protocol_sha256':sha(ROOT/'docs/receptor-calibration-v3.md'),'source_code_sha256':sha(__file__),
          'v2_code_sha256':sha(ROOT/'research/calibrate_receptor_v2.py'),'helper_code_sha256':sha(ROOT/'research/calibrate_receptor_recordings.py'),
          'betas':BETAS,'outer_folds':v2['outer_folds'],'reserved_tests_read':False}
    args.output.with_name(args.output.stem+'-preregistration.json').write_text(json.dumps(lock,indent=2)+'\n')
    animals=[str(i) for i in range(1,17)]
    segments,quality=load_segments(args.data_dir/file,{'development':animals})
    cache={}
    def candidates(metadata):
        fixed={**metadata['passive']['config'],**metadata['drive']['config']};out=[]
        for beta in BETAS:
            c={**fixed,'beta':beta};key=json.dumps(c,sort_keys=True)
            if key not in cache:cache[key]=collect(segments,c)
            out.append((c,cache[key]))
        return out
    predictions={'tonic_candidate':{},'movement_only':{}};fold_results=[]
    for fold in v2['fold_results']:
        heldout=fold['heldout'];train=[a for a in animals if a not in heldout];choices=candidates(fold['calibration']);record={}
        for name,movement_only in [('tonic_candidate',False),('movement_only',True)]:
            c,s,h,cv=select(choices,train,movement_only)
            predictions[name].update(evaluate(s,heldout,h));record[name]={**packed(c,h),'cv':cv}
        fold_results.append({'heldout':heldout,'models':record})
        print('Outer heldout',heldout,{k:mean_mse({a:r for a,r in v.items() if a in heldout}) for k,v in predictions.items()},flush=True)
    predictions.update({('v2' if name=='candidate' else name):rows for name,rows in v2['outer_predictions'].items()})
    strongest=min((m for m in predictions if m!='tonic_candidate'),key=lambda m:mean_mse(predictions[m]))
    final={};final_choices=candidates(v2['final_calibration'])
    for name,movement_only in [('tonic_candidate',False),('movement_only',True)]:
        c,s,h,cv=select(final_choices,animals,movement_only);final[name]={**packed(c,h),'cv':cv}
    report={**lock,'quality':quality,'fold_results':fold_results,'outer_predictions':predictions,
            'mse':{m:mean_mse(r) for m,r in predictions.items()},'strongest_control':strongest,
            'candidate_vs_strongest':paired_interval(predictions['tonic_candidate'],predictions[strongest]),
            'candidate_vs_movement_only':paired_interval(predictions['tonic_candidate'],predictions['movement_only']),
            'frozen_models':final,'production_promotion':False,
            'limits':['Tonic sensory activity is an assumption, not identified from passive calcium.',
                      'Behavior-gated calcium does not identify 9A spikes/receptor kinetics.',
                      'All outcomes are development data; no new test claims or parameter transfers.']}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('mse','strongest_control','candidate_vs_strongest','candidate_vs_movement_only','frozen_models')},indent=2))

if __name__=='__main__':main()
