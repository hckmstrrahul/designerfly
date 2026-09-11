import json,time
import numpy as np
from core import ROOT,target
from embodied import CENTER,SCALE
from runtime import load_policies,DrawingSession

planner,motor=load_policies();results=[];start=time.perf_counter()
for shape in range(3):
    for condition in ['normal','perturbed','feedback_removed','core_removed']:
        session=DrawingSession(shape,planner,motor,offset=np.array([.06,-.04,.04]) if condition=='perturbed' else None)
        errors=[];tracking=[];contact=[];recovery=[];before_push=[]
        for i in range(700):
            push=np.array([.8,-.5,.5]) if condition=='perturbed' and 5<session.env.data.time<5.10 else None
            f=session.step(ablated=condition=='core_removed',feedback=condition!='feedback_removed',push=push)
            if 1.4<f['time']<13.2:
                p=np.array(f['tip'])[[0,1]];truth=CENTER[:2]+target([shape],[f['phase']])[0]*SCALE
                e=float(np.linalg.norm(p-truth));errors.append(e);tracking.append(float(np.linalg.norm(p-np.array(f['reference'])[:2])));contact.append(f['contact'])
                if 5.6<f['time']<6.1:recovery.append(e)
                if 4.5<f['time']<4.9:before_push.append(e)
        result={'shape':['rectangle','circle','triangle'][shape],'condition':condition,'rmse':float(np.sqrt(np.mean(np.array(errors)**2))),'max_error':max(errors),'tracking_rmse':float(np.sqrt(np.mean(np.array(tracking)**2))),'contact_fraction':float(np.mean(contact)),'recovery_error':float(np.mean(recovery)),'before_push_error':float(np.mean(before_push))}
        results.append(result);print(json.dumps(result),flush=True)
normal=[r for r in results if r['condition']=='normal'];perturbed=[r for r in results if r['condition']=='perturbed']
passed=all(r['rmse']<.035 and r['contact_fraction']>.95 for r in normal) and all(r['recovery_error']<.05 for r in perturbed)
report={'engine':'MuJoCo','length_unit':'model millimetres; forces and time are normalized, not biologically calibrated','results':results,'seconds':time.perf_counter()-start,'passed':passed,'scope':'Tethered 3-DOF foreleg; rigid attached stylus; neural incremental joint commands; contact-gated ink','criteria':'Normal RMSE < 0.035 model mm, contact > 95%; perturbed recovery error < 0.05 model mm','feedback':'Joint angles, velocities, actual tip error and contact force feed the motor circuit every 20 ms','teacher_at_inference':False}
(ROOT/'research/results/embodied-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({'passed':passed}),flush=True)
