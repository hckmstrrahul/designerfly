"""Held-out layouts, physical pen lifts, independent motor parity and ablations."""
import json,time
import numpy as np
import torch
from core import ROOT,Circuit,target,G
from composition import CompositionSession,load_placement,load_composition_motor,place_point
from placement import sample_placements
from embodied import CENTER,observation,inverse_kinematics,forward,PAPER_Z,TIP_RADIUS

planner=load_placement();motor=load_composition_motor();rng=np.random.default_rng(90377)
layouts=[]
# A reviewable UI study and unrelated test layouts never used for training.
layouts.append([dict(shape=0,x=0,y=-.64,width=1.55,height=.28),dict(shape=1,x=-.52,y=-.03,width=.43,height=.43),dict(shape=0,x=.29,y=-.03,width=.78,height=.43),dict(shape=0,x=0,y=.6,width=1.55,height=.38)])
for trial in range(7):
    boxes=sample_placements(4,rng);strokes=[]
    for i,b in enumerate(boxes):
        s=dict(shape=(trial+i)%3,x=float(b[0]),y=float(b[1]),width=float(b[2]),height=float(b[3]))
        if s['shape']==1:
            s['height']=s['width']=min(s['width'],s['height'])
        strokes.append(s)
    layouts.append(strokes)
results=[];poses=[];start=time.perf_counter()
for trial,strokes in enumerate(layouts):
    session=CompositionSession(strokes,planner,motor);errors=[[] for _ in strokes];contacts=[[] for _ in strokes];transition_contacts=0;travel_frames=0;last_stage='travel'
    for i in range(7000):
        f=session.step();index=f['stroke_index'];s=strokes[index]
        if i%5==0:poses.append(f)
        if f['drawing']:
            truth=CENTER[:2]+place_point(target([s['shape']],[f['stroke_phase']])[0],s)*.4
            errors[index].append(float(np.linalg.norm(np.array(f['tip'])[:2]-truth)));contacts[index].append(f['contact'])
        if f['stage']=='travel':travel_frames+=1;transition_contacts+=int(f['contact'])
        if f['done']:break
    for index,s in enumerate(strokes):
        result={'layout':trial,'stroke':index,'spec':s,'rmse':float(np.sqrt(np.mean(np.square(errors[index])))),'max_error':max(errors[index],default=99),'contact_fraction':float(np.mean(contacts[index])),'completed':session.done,'travel_contacts':transition_contacts}
        results.append(result)
    print(json.dumps({'layout':trial,'completed':session.done,'max_rmse':max(r['rmse'] for r in results if r['layout']==trial),'travel_contacts':transition_contacts}),flush=True)

interventions=[]
for condition in ['normal','core_removed','feedback_removed']:
    session=CompositionSession(layouts[0][:1],planner,motor);errors=[]
    for _ in range(600):
        f=session.step(ablated=condition=='core_removed',feedback=condition!='feedback_removed')
        if f['drawing']:errors.append(float(np.linalg.norm(np.array(f['tip'])[:2]-np.array(f['reference'])[:2])))
    interventions.append({'condition':condition,'tracking_rmse':float(np.sqrt(np.mean(np.square(errors))))})

net=Circuit(seed=421,outputs=3);net.load_state_dict(torch.load(ROOT/'research/results/composition-motor.pt',weights_only=False)['state_dict'])
base=Circuit(seed=421,outputs=3);base.load_state_dict(torch.load(ROOT/'research/results/motor.pt',weights_only=False)['state_dict'])
refs=np.c_[rng.uniform(1.13,1.97,2048),rng.uniform(-.4,.4,2048),rng.uniform(PAPER_Z-.02,1.16,2048)]
desired=np.array([inverse_kinematics(r) for r in refs]);q=desired+rng.normal(0,.04,(2048,3));dq=rng.normal(0,.22,(2048,3));tip=forward(q);force=np.maximum(0,(PAPER_Z+TIP_RADIUS-tip[:,2])*4)
x=np.array([observation(r,a,b,c,f) for r,a,b,c,f in zip(refs,q,dq,tip,force)]);y=np.clip((desired-q)*8-dq*.12,-1,1)
with torch.no_grad():
    pred,state=net(torch.tensor(x),return_state=True);old=base(torch.tensor(x));ablated=net(torch.tensor(x),ablated=True)
scores={'before_refinement_rmse':float(np.sqrt(np.mean((old.numpy()-y)**2))),'trained_rmse':float(np.sqrt(np.mean((pred.numpy()-y)**2))),'ablated_rmse':float(np.sqrt(np.mean((ablated.numpy()-y)**2)))}
for i in [0,127,1000]:
    action,rate=motor(x[i]);np.testing.assert_allclose(action,pred[i].numpy(),atol=1e-5);np.testing.assert_allclose(rate,state[i].numpy(),atol=1e-5)
fixed=all(torch.equal(v,base.state_dict()[k]) for k,v in net.state_dict().items() if k not in ['gain','leak','bias'])
passed=all(r['completed'] and r['rmse']<.035 and r['contact_fraction']>.95 and r['travel_contacts']==0 for r in results) and fixed and all(r['tracking_rmse']>interventions[0]['tracking_rmse']*5 for r in interventions[1:])
report={'passed':passed,'criteria':'Every held-out stroke RMSE < .035 model mm, >95% contact; no travel contacts; completed layouts; ablations >5x normal error','layouts':len(layouts),'strokes':len(results),'results':results,'interventions':interventions,'scores':scores,'fixed_interfaces':fixed,'pytorch_runtime_parity':True,'seconds':time.perf_counter()-start,'scope':'Generated UI-like and held-out random layouts within x/y [-1,1] with .24–1.72 bounding-box dimensions. Geometry is placed explicitly; learned feedback commands physical joints.'}
(ROOT/'research/results/composition-validation.json').write_text(json.dumps(report,indent=2))
(ROOT/'research/results/composition-poses.json').write_text(json.dumps(poses))
print(json.dumps({k:v for k,v in report.items() if k not in ['results']}),flush=True)
if not passed:raise SystemExit(1)
