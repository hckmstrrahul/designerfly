"""Independent physical acceptance checks for each trained network size."""
import argparse,json,time
import numpy as np
from core import ROOT,G,Circuit,numpy_infer,target
import torch
from runtime import DrawingSession,load_policies
from composition import CompositionSession,place_point
from placement import sample_placements
from embodied import CENTER,SCALE

p=argparse.ArgumentParser();p.add_argument('--sizes',nargs='+',type=int,default=[1024,2048,4096]);args=p.parse_args()
planner,_=load_policies();rng=np.random.default_rng(61497)
search=[dict(shape=0,x=0,y=-.72,width=1.64,height=.28),dict(shape=1,x=-.65,y=-.15,width=.28,height=.28),dict(shape=0,x=.2,y=-.15,width=1.2,height=.38),dict(shape=1,x=-.65,y=.39,width=.28,height=.28),dict(shape=0,x=.2,y=.39,width=1.2,height=.38),dict(shape=0,x=0,y=.8,width=1.64,height=.24)]
layouts=[search]
for trial in range(7):
    layout=[]
    for i,b in enumerate(sample_placements(4,rng)):
        s=dict(shape=(trial+i)%3,x=float(b[0]),y=float(b[1]),width=float(b[2]),height=float(b[3]))
        if s['shape']==1:s['height']=s['width']=min(s['height'],s['width'])
        layout.append(s)
    layouts.append(layout)
summary=[]
for size in args.sizes:
    graph=G if size==1024 else np.load(ROOT/f'research/data/circuit-{size}.npz')
    net=Circuit(seed=421,outputs=3,graph=graph,gain_mode='softplus');net.load_state_dict(torch.load(ROOT/f'research/results/expanded-motor-{size}.pt',weights_only=False)['state_dict']);motor=numpy_infer(net)
    results=[];poses=[];start=time.perf_counter()
    for trial,strokes in enumerate(layouts):
        session=CompositionSession(strokes,planner,motor);errors=[[] for _ in strokes];contacts=[[] for _ in strokes];travel_contacts=0
        for i in range(8000):
            f=session.step();index=f['stroke_index'];s=strokes[index]
            if i%5==0:poses.append(f)
            if f['drawing']:
                truth=CENTER[:2]+place_point(target([s['shape']],[f['stroke_phase']])[0],s)*.4
                errors[index].append(float(np.linalg.norm(np.array(f['tip'])[:2]-truth)));contacts[index].append(f['contact'])
            if f['stage']=='travel':travel_contacts+=int(f['contact'])
            if f['done']:break
        for i,s in enumerate(strokes):
            results.append(dict(layout=trial,stroke=i,rmse=float(np.sqrt(np.mean(np.square(errors[i])))),contact_fraction=float(np.mean(contacts[i])),completed=session.done,travel_contacts=travel_contacts))
    single=[]
    for shape in range(3):
        for condition in ['normal','perturbed','core_removed','feedback_removed']:
            session=DrawingSession(shape,planner,motor,offset=np.array([.06,-.04,.04]) if condition=='perturbed' else None);errors=[];contact=[];recovery=[]
            for i in range(700):
                t=session.env.data.time
                f=session.step(ablated=condition=='core_removed',feedback=condition!='feedback_removed',push=np.array([.8,-.5,.5]) if condition=='perturbed' and 5<t<5.1 else None)
                if i%5==0 and condition in ['normal','perturbed']:poses.append(f)
                if 1.4<f['time']<13.2:
                    err=float(np.linalg.norm(np.array(f['tip'])[:2]-(CENTER[:2]+target([shape],[f['phase']])[0]*SCALE)));errors.append(err);contact.append(f['contact'])
                    if 5.6<f['time']<6.1:recovery.append(err)
            single.append(dict(shape=shape,condition=condition,rmse=float(np.sqrt(np.mean(np.square(errors)))),contact_fraction=float(np.mean(contact)),recovery_error=float(np.mean(recovery))))
    normal=[r for r in single if r['condition']=='normal'];perturbed=[r for r in single if r['condition']=='perturbed'];ablated=[r for r in single if r['condition'] in ['core_removed','feedback_removed']]
    passed=all(r['completed'] and r['rmse']<.035 and r['contact_fraction']>.95 and r['travel_contacts']==0 for r in results) and all(r['rmse']<.035 and r['contact_fraction']>.95 for r in normal) and all(r['recovery_error']<.05 for r in perturbed) and all(r['rmse']>max(v['rmse'] for v in normal)*5 for r in ablated)
    report=dict(neurons=size,passed=passed,strokes=len(results),layouts=len(layouts),results=results,single=single,worst_stroke_rmse=max(r['rmse'] for r in results),mean_stroke_rmse=float(np.mean([r['rmse'] for r in results])),seconds=time.perf_counter()-start,criteria='Each stroke RMSE < .035 model mm, >95% contact, no travel contact, completed; normal single shapes meet same limits; recovery < .05; ablation >5x normal error.')
    (ROOT/f'research/results/expansion-validation-{size}.json').write_text(json.dumps(report,indent=2))
    (ROOT/f'research/results/expansion-poses-{size}.json').write_text(json.dumps(poses))
    summary.append({k:v for k,v in report.items() if k not in ['results','single']});print(json.dumps(summary[-1]),flush=True)
summary=[]
for size in [1024,2048,4096]:
    path=ROOT/f'research/results/expansion-validation-{size}.json'
    if path.exists():summary.append({k:v for k,v in json.loads(path.read_text()).items() if k not in ['results','single']})
(ROOT/'research/results/expansion-acceptance.json').write_text(json.dumps(summary,indent=2))
