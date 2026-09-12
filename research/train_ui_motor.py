"""Offline UI curriculum for the spiking motor readout, never internal weights.

Writes candidates only. Deployment requires independent physical acceptance.
A validated rate teacher (or optional IK teacher) labels offline demonstrations.
Neither is called by the runtime spiking controller.
"""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
import argparse, hashlib, json, time
from pathlib import Path
import numpy as np
from spiking_motor import SpikingMotor, CHECKPOINT
from composition import CompositionSession
from embodied import inverse_kinematics, CENTER

def curriculum(rng, count, mixed=False):
    for i in range(count):
        x,y=rng.uniform(-.48,.48,2)
        w,h=rng.uniform(.18,.72,2)
        if i%4==0: points=[[-.5,0],[.5,0]]
        elif i%4==1: points=[[0,-.5],[0,.5]]
        elif i%4==2: points=[[-.5,-.5],[.5,-.5],[.5,.5],[-.5,.5],[-.5,-.5]]
        else:
            points=[]
            for cx,cy,angle in [(.36,-.36,-90),(.36,.36,0),(-.36,.36,90),(-.36,-.36,180)]:
                for a in np.linspace(angle,angle+90,9)*np.pi/180: points.append([cx+.14*np.cos(a),cy+.14*np.sin(a)])
            points.append(points[0])
        if mixed:
            w,h=rng.uniform(.08,.85,2)
            x,y=rng.uniform(-1+np.array([w,h])/2,1-np.array([w,h])/2)
            if i%5==0:
                yield [dict(shape=int(rng.integers(3)),x=float(x),y=float(y),width=float(w),height=float(h))]
                continue
        yield [dict(shape=0,x=float(x),y=float(y),width=float(w),height=float(h),points=points)]

def main():
    p=argparse.ArgumentParser();p.add_argument('--checkpoint',type=Path,default=CHECKPOINT)
    p.add_argument('--output-dir',type=Path,default=Path('work/ui-training'))
    p.add_argument('--curriculum',choices=['ui','mixed'],default='ui')
    p.add_argument('--elbow-bias',type=float,default=0.,help='Offline-selected readout intercept calibration')
    p.add_argument('--blend',type=float,default=1.,help='Fraction of newly trained readout; retain the baseline for the rest')
    p.add_argument('--rollouts',type=int,default=32);p.add_argument('--teacher',choices=['rate','ik'],default='rate');args=p.parse_args()
    from active_motor import policy_or
    from composition import load_composition_motor, load_placement
    teacher=policy_or(load_composition_motor()) if args.teacher=='rate' else None
    planner=load_placement()
    if not 0 < args.blend <= 1: p.error('--blend must be in (0,1]')
    if not np.isfinite(args.elbow_bias) or abs(args.elbow_bias) > .1: p.error('--elbow-bias must be finite and within ±0.1')
    args.output_dir.mkdir(parents=True,exist_ok=True)
    with np.load(args.checkpoint) as d: base={k:d[k].copy() for k in d.files}
    rng=np.random.default_rng(73192);X=[];Y=[];DX=[];start=time.time()
    for index,strokes in enumerate(curriculum(rng,args.rollouts,args.curriculum=='mixed')):
        motor=SpikingMotor(args.checkpoint);previous=None
        def demonstration(obs,ablated=False):
            nonlocal previous
            f=motor.features(obs);X.append(f)
            reference=obs[:3]*.5+CENTER
            q=obs[3:6]*1.5+np.array([0.,-.7,1.5]);velocity=obs[6:9]/.05
            target=teacher(obs)[0] if teacher is not None else np.clip((inverse_kinematics(reference)-q)*8-velocity*.12,-1,1)
            Y.append(target)
            if previous is not None: DX.append(f-previous)
            previous=f.copy()
            # Collect both accurate teacher states and the existing policy's errors.
            action=target if index%2==0 else np.clip(((f-base['mean'])/base['scale'])@base['decoder'],-1,1)
            return action, np.minimum(motor.circuit.rate/100,1)
        demonstration.contact_height_offset=motor.contact_height_offset
        demonstration.draw_duration_scale=motor.draw_duration_scale
        demonstration.learned_duration_scale=motor.learned_duration_scale
        session=CompositionSession(strokes,planner,demonstration)
        for _ in range(2500):
            if session.step()['done']:break
        print(json.dumps({'rollout':index+1,'samples':len(X),'seconds':round(time.time()-start,1)}),flush=True)
    x=np.asarray(X);y=np.asarray(Y);mean=x.mean(0);scale=x.std(0).clip(.01);mean[-1]=0;scale[-1]=1
    z=(x-mean)/scale;dz=np.asarray(DX)/scale
    # Penalize rapid readout changes across adjacent states, including travel and turns.
    gram=z.T@z;rhs=z.T@y
    reports=[]
    for penalty in [1.,10.,100.]:
        for smooth in [0.,5.,25.]:
            decoder=np.linalg.solve(gram+penalty*np.eye(z.shape[1])+smooth*(dz.T@dz),rhs)
            dest=args.output_dir/f'candidate-r{penalty:g}-s{smooth:g}.npz'
            fitted=decoder.copy()
            output_mean,output_scale=mean,scale
            if args.blend < 1:
                converted=(base['scale']/scale)[:,None]*decoder
                converted[-1]+=((base['mean']-mean)/scale)@decoder
                decoder=(1-args.blend)*base['decoder']+args.blend*converted
                output_mean,output_scale=base['mean'],base['scale']
            decoder[-1,2]+=args.elbow_bias
            np.savez(dest,projection=base['projection'],decoder=decoder,mean=output_mean,scale=output_scale,baseline=base['baseline'])
            reports.append({'checkpoint':str(dest),'ridge':penalty,'smoothness':smooth,'blend':args.blend,'action_training_rmse':float(np.mean((z@fitted-y)**2)**.5)})
    report={'seed':73192,'blend':args.blend,'elbow_bias':args.elbow_bias,'rollouts':args.rollouts,'samples':len(X),'baseline_sha256':hashlib.sha256(args.checkpoint.read_bytes()).hexdigest(),'internal_weights_frozen':True,'input_projection_frozen':True,'teacher':args.teacher+' offline feedback controller; half teacher rollouts, half existing motor rollouts','curriculum':args.curriculum+': horizontal/vertical lines, rectangles, rounded rectangles; varied size and location; mixed adds full-paper positions, tiny details and original learned shapes','runtime_ik':False,'seconds':time.time()-start,'candidates':reports}
    (args.output_dir/'training.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
if __name__=='__main__':main()
