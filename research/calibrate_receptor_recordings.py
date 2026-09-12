"""Animal-held-out phenomenological hook calcium suppression calibration.

This does not identify receptor, synapse, or measured 9A input parameters.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq
from scipy.signal import lfilter

ROOT = Path(__file__).resolve().parents[1]
MAIN = 'hook_flexion_01_treadmill_platform.parquet'
PASSIVE = 'hook_flexion_01_magnet.parquet'
TAU_ON, TAU_OFF = .03, .30
THRESHOLDS = (-5., -20., -50., -100., -200.)
GATE_TAUS = (.03, .10, .30, 1.)
BETAS = (.5, 1., 2., 5., 10.)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lowpass(signal, dt, tau):
    decay = np.exp(-dt/tau)
    return lfilter([1-decay], [1,-decay], signal)


def calcium(signal, dt):
    # Cascade is a normalized difference-of-exponentials impulse kernel.
    return lowpass(lowpass(signal, dt, TAU_ON),dt,TAU_OFF)


def load_segments(path, split, stride=3, passive=False):
    schema = pq.read_schema(path).names
    columns = ['animal_id','trial','roi','time','calcium','L1C_flex_vel','analyze']
    if not passive:
        columns.append('L1_move')
    table = pq.read_table(path,columns=columns).sort_by([(k,'ascending') for k in ['animal_id','trial','roi','time']])
    arrays = {k:table[k].to_numpy() for k in columns}
    boundaries = np.zeros(len(table),dtype=bool);boundaries[0]=True
    for k in ['animal_id','trial','roi']:
        boundaries[1:] |= arrays[k][1:] != arrays[k][:-1]
    ranges = np.r_[np.flatnonzero(boundaries),len(table)]
    segments=[];group_counts={};irregular=0;retained=0
    assignments = {a:part for part,animals in split.items() for a in animals}
    for start,end in zip(ranges[:-1],ranges[1:]):
        animal=str(int(arrays['animal_id'][start]));part=assignments[animal]
        times=arrays['time'][start:end]
        velocity=arrays['L1C_flex_vel'][start:end]
        move=np.zeros(len(times)) if passive else arrays['L1_move'][start:end]
        valid=np.isfinite(times)&np.isfinite(velocity)&np.isfinite(move)
        dt=np.median(np.diff(times)[np.diff(times)>0]) if len(times)>1 else 1/300
        breaks=np.r_[True,(np.diff(times)<=0)|(np.diff(times)>max(.02,3*dt))|~valid[1:]|~valid[:-1],True]
        edges=np.flatnonzero(breaks)
        for left,right in zip(edges[:-1],edges[1:]):
            if right-left<2 or not valid[left:right].all():continue
            local_dt=float(np.median(np.diff(times[left:right])))
            if np.max(np.abs(np.diff(times[left:right])-local_dt))>local_dt*.01:
                irregular+=1
                raise ValueError('Irregular sampling >1%; resampling needs an explicit protocol')
            score=np.zeros(right-left,dtype=bool);score[::stride]=True
            score &= arrays['analyze'][start+left:start+right]==1
            score &= np.isfinite(arrays['calcium'][start+left:start+right])
            # Retain excluded frames for filtering; reset only across trial/ROI/gaps.
            segment={'animal':animal,'part':part,'dt':local_dt,'velocity':velocity[left:right],
                     'move':np.clip(move[left:right],0,1),'y':arrays['calcium'][start+left:start+right], 'score':score}
            segments.append(segment);retained+=right-left
            group_counts[animal]=group_counts.get(animal,0)+int(score.sum())
    return segments,{'raw_frames':len(table),'dynamic_frames':int(retained),'segments':len(segments),'scored_frames_by_animal':group_counts,'irregular_segments':irregular,'score_stride':stride}


def features(segments,threshold,tau,beta):
    return [calcium((s['velocity']<threshold).astype(float)/(1+beta*lowpass(s['move'],s['dt'],tau)),s['dt']) for s in segments]


def fit_affine(segments,x):
    # Each training animal has total weight one, independent of recording length.
    stats={}
    for s,p in zip(segments,x):
        if s['part']!='train':continue
        m=s['score'];xx=p[m];yy=s['y'][m]
        if not len(xx):continue
        stats.setdefault(s['animal'],np.zeros(6))[:] += [len(xx),xx.sum(),yy.sum(),xx@xx,xx@yy,yy@yy]
    matrix=np.zeros((2,2));rhs=np.zeros(2)
    for n,sx,sy,sxx,sxy,_ in stats.values():
        matrix += [[sxx/n,sx/n],[sx/n,1]];rhs += [sxy/n,sy/n]
    amplitude,offset=np.linalg.lstsq(matrix,rhs,rcond=None)[0]
    # Negative activation-to-calcium amplitude is outside this model's hypothesis.
    if amplitude<0:
        amplitude=0.;offset=float(np.mean([v[2]/v[0] for v in stats.values()]))
    return float(amplitude),float(offset)


def evaluate(segments,x,amplitude,offset,part):
    sums={}
    for s,p in zip(segments,x):
        if s['part']!=part:continue
        for condition in ['all','active','not_actively_moving']:
            m=s['score'].copy()
            if condition=='active':m &= s['move']>.5
            elif condition=='not_actively_moving':m &= s['move']<=.5
            if not m.any():continue
            error=amplitude*p[m]+offset-s['y'][m]
            key=(s['animal'],condition);prediction=amplitude*p[m]+offset;target=s['y'][m]
            sums.setdefault(key,np.zeros(8))[:] += [len(error),error@error,np.abs(error).sum(),prediction.sum(),target.sum(),prediction@prediction,target@target,prediction@target]
    per={}
    for (animal,condition),(n,sse,sae,sp,sy,spp,syy,spy) in sums.items():
        vy=syy-sy*sy/n;vp=spp-sp*sp/n
        correlation=float((spy-sp*sy/n)/np.sqrt(vy*vp)) if amplitude!=0 and vy>1e-10 and vp>1e-10 else None
        per.setdefault(animal,{})[condition]={'frames':int(n),'mse':float(sse/n),'rmse':float(np.sqrt(sse/n)),'mae':float(sae/n),'pearson_r':correlation,'r2_against_animal_mean':float(1-sse/vy) if vy>1e-10 else None}
    aggregate={}
    for condition in ['all','active','not_actively_moving']:
        rows=[a[condition] for a in per.values() if condition in a and a[condition]['frames']>=30]
        if rows:aggregate[condition]={'animals':len(rows),'mse':float(np.mean([r['mse'] for r in rows])),'rmse':float(np.sqrt(np.mean([r['mse'] for r in rows])))}
    return {'equal_animal':aggregate,'per_animal':per}


def bootstrap(gated,baseline):
    animals=sorted(set(gated['per_animal'])&set(baseline['per_animal']))
    differences=np.array([baseline['per_animal'][a]['all']['mse']-gated['per_animal'][a]['all']['mse'] for a in animals])
    rng=np.random.default_rng(937401)
    samples=rng.choice(differences,size=(10000,len(differences)),replace=True).mean(1)
    return {'animals':animals,'n_animals':len(animals),'baseline_minus_gated_mse':float(differences.mean()),'animal_bootstrap_95_interval':np.quantile(samples,[.025,.975]).tolist(),'replicates':10000,'limits':'Only two main test animals: interval is descriptive and cannot establish population-level certainty.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--split',type=Path,default=ROOT/'research/results/receptor-recording-split.json')
    parser.add_argument('--output',type=Path,default=ROOT/'research/results/receptor-calibration.json')
    args=parser.parse_args()
    locked=json.loads(args.split.read_text());split=locked['split']
    expected={r['file']:r['sha256'] for r in locked['recordings']}
    for name in [MAIN,PASSIVE]:
        if sha(args.data_dir/name)!=expected[name]:raise ValueError('Input checksum differs from locked preflight: '+name)
    segments,quality=load_segments(args.data_dir/MAIN,split)
    candidates=[]
    # Candidate choices are made on validation only; test targets never enter fit/selection.
    for threshold in THRESHOLDS:
        for tau,beta in [(.1,0.)]+[(t,b) for t in GATE_TAUS for b in BETAS]:
            x=features(segments,threshold,tau,beta)
            amplitude,offset=fit_affine(segments,x)
            val=evaluate(segments,x,amplitude,offset,'validation')
            candidate={'threshold_degrees_per_second':threshold,'gate_tau_seconds':tau,'beta':beta,'amplitude':amplitude,'offset':offset,'validation_mse':val['equal_animal']['all']['mse']}
            candidates.append(candidate)
        print('Completed validation grid threshold',threshold,flush=True)
    choices={'baseline':min((c for c in candidates if c['beta']==0),key=lambda c:c['validation_mse']),
             'gated':min((c for c in candidates if c['beta']>0),key=lambda c:c['validation_mse'])}
    report={'source_code_sha256':sha(__file__),'production_promotion':False,'scope':'Phenomenological hook calcium suppression, not receptor/synapse or measured 9A input identification',
            'source_doi':'10.5061/dryad.gqnk98t16','source_sha256':{n:sha(args.data_dir/n) for n in [MAIN,PASSIVE,'README.md']},
            'split_sha256':sha(args.split),'split':split,'quality':quality,'nontransferability':'Gate input is observed binary movement, not measured 9A neural activity. Fitted beta/tau cannot be inserted into a spike-driven runtime gate: units and input dynamics differ.', 'kernel':{'tau_on_seconds':TAU_ON,'tau_off_seconds':TAU_OFF,'implementation':'Two causal unit-gain low-pass filters; zero initial state per segment. Discrete cascade approximates the normalized difference-of-exponentials kernel with approximately one sampling-interval onset difference. Fixed timescales, not inferred.'},
            'grid':{'thresholds':THRESHOLDS,'gate_taus':GATE_TAUS,'betas':BETAS},'validation_candidates':candidates,'models':{}}
    for name,c in choices.items():
        x=features(segments,c['threshold_degrees_per_second'],c['gate_tau_seconds'],c['beta'])
        report['models'][name]={'parameters':c,**{part:evaluate(segments,x,c['amplitude'],c['offset'],part) for part in ['train','validation','test']}}
    training_targets={}
    for s in segments:
        if s['part']=='train':training_targets.setdefault(s['animal'],[]).append(s['y'][s['score']])
    constant=float(np.mean([np.concatenate(v).mean() for v in training_targets.values()]))
    report['training_mean_constant']={'value':constant,**{part:evaluate(segments,[np.zeros(len(s['y'])) for s in segments],0.,constant,part) for part in ['train','validation','test']}}
    report['test_comparison']=bootstrap(report['models']['gated']['test'],report['models']['baseline']['test'])
    passive,passive_quality=load_segments(args.data_dir/PASSIVE,split,passive=True)
    report['external_passive']={'scope':'Secondary transfer without refitting; fully restrained L1_move set to zero; acquisition/normalization domain may differ','quality':passive_quality,'models':{}}
    for name,c in choices.items():
        x=features(passive,c['threshold_degrees_per_second'],c['gate_tau_seconds'],c['beta'])
        report['external_passive']['models'][name]=evaluate(passive,x,c['amplitude'],c['offset'],'test')
    report['conclusion']='Held-out MSE improves descriptively; not mechanistic identification' if report['test_comparison']['baseline_minus_gated_mse']>0 else 'Suppression model did not improve held-out MSE; do not claim calibrated predictive benefit'
    report['identifiability_notes']=['Observed movement proxy does not identify receptor or spike-driven gate parameters.', 'Test uncertainty is based on two animals; do not tune further on these exposed outcomes.']
    if choices['gated']['beta'] in [min(BETAS),max(BETAS)] or choices['gated']['gate_tau_seconds'] in [min(GATE_TAUS),max(GATE_TAUS)]:
        report['identifiability_notes'].append('Selected gate beta and/or tau is at a grid boundary; not precisely identified.')
    if choices['baseline']['amplitude']==0:
        report['identifiability_notes'].append('Nongated amplitude collapsed to zero; baseline threshold is not identified.')
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'choices':choices,'test':report['test_comparison'],'conclusion':report['conclusion']},indent=2),flush=True)

if __name__=='__main__':main()
