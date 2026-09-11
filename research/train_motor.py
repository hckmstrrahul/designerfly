"""Train a measured-circuit feedback policy from offline actuator demonstrations."""
import argparse,json,time
import numpy as np
import torch
from core import Circuit,ROOT,numpy_infer
from embodied import Foreleg,CENTER,PAPER_Z,TIP_RADIUS,inverse_kinematics,forward,observation

p=argparse.ArgumentParser();p.add_argument('--steps',type=int,default=6000);p.add_argument('--refine',action='store_true');p.add_argument('--rollouts',action='store_true');p.add_argument('--composition',action='store_true');args=p.parse_args()
torch.set_num_threads(6);torch.manual_seed(421);rng=np.random.default_rng(421)
net=Circuit(seed=421,input_size=16,outputs=3)
initial={k:v.clone() for k,v in net.state_dict().items()}
if args.refine:net.load_state_dict(torch.load(ROOT/('research/results/composition-motor.pt' if args.composition and (ROOT/'research/results/composition-motor.pt').exists() else 'research/results/motor.pt'),weights_only=False)['state_dict'])
rollout_x=[];rollout_y=[]
if args.rollouts:
    from runtime import DrawingSession,load_policies
    planner,_=load_policies();policy=numpy_infer(net)
    for shape in range(3):
        session=DrawingSession(shape,planner,policy)
        for i in range(700):
            f=session.step();ref=np.array(f['reference']);q=np.array(f['q']);dq=np.array(f['qvel'])
            rollout_x.append(observation(ref,q,dq,f['tip'],f['force']))
            rollout_y.append(np.clip((inverse_kinematics(ref)-q)*8-dq*.12,-1,1))
    rollout_x=np.array(rollout_x);rollout_y=np.array(rollout_y)
if args.composition:
    from composition import CompositionSession,load_placement
    from placement import sample_placements
    planner=load_placement();policy=numpy_infer(net)
    for layout in range(8):
        boxes=sample_placements(4,rng)
        strokes=[dict(shape=int(rng.integers(0,3)),x=float(b[0]),y=float(b[1]),width=float(b[2]),height=float(b[3])) for b in boxes]
        session=CompositionSession(strokes,planner,policy)
        for i in range(6000):
            f=session.step();ref=np.array(f['reference']);q=np.array(f['q']);dq=np.array(f['qvel'])
            rollout_x.append(observation(ref,q,dq,f['tip'],f['force']))
            rollout_y.append(np.clip((inverse_kinematics(ref)-q)*8-dq*.12,-1,1))
            if f['done']:break
    rollout_x=np.array(rollout_x);rollout_y=np.array(rollout_y)
    print(json.dumps({'composition_demonstrations':len(rollout_x)}),flush=True)
def batch(n,rng):
    refs=np.c_[rng.uniform(1.07,1.97,n),rng.uniform(-.43,.43,n),rng.uniform(PAPER_Z-.04,1.17,n)]
    scale=np.where(rng.random((n,1))<.8,.035,.14) if args.refine else .14
    desired=np.array([inverse_kinematics(r) for r in refs]);q=desired+rng.normal(0,1,(n,3))*scale;dq=rng.normal(0,.25,(n,3));tip=forward(q)
    force=np.maximum(0,(PAPER_Z+TIP_RADIUS-tip[:,2])*4)
    obs=np.array([observation(r,a,b,c,f) for r,a,b,c,f in zip(refs,q,dq,tip,force)])
    commands=np.clip((desired-q)*8-dq*.12,-1,1)
    if args.rollouts or args.composition:
        indices=rng.integers(0,len(rollout_x),n//2)
        obs[:n//2]=rollout_x[indices];commands[:n//2]=rollout_y[indices]
    return torch.tensor(obs),torch.tensor(commands,dtype=torch.float32)
vx,vy=batch(1024,np.random.default_rng(884));opt=torch.optim.Adam(net.parameters(),lr=.003 if args.refine else .012);history=[];start=time.perf_counter()
with torch.no_grad():before=float((net(vx)-vy).square().mean().sqrt())
for step in range(args.steps):
    x,y=batch(128,rng);pred=net(x);loss=(pred-y).square().mean()
    opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(net.parameters(),1);opt.step()
    if step in [args.steps//2,args.steps*4//5]:
        for g in opt.param_groups:g['lr']*=.3
    if step%400==0 or step==args.steps-1:
        with torch.no_grad():error=float((net(vx)-vy).square().mean().sqrt())
        rec={'step':step+1,'loss':float(loss),'validation_rmse':error,'seconds':time.perf_counter()-start};history.append(rec);print(json.dumps(rec),flush=True)
with torch.no_grad():after=float((net(vx)-vy).square().mean().sqrt());ablated=float((net(vx,ablated=True)-vy).square().mean().sqrt())
torch.save({'state_dict':net.state_dict(),'initial':initial},ROOT/('research/results/composition-motor.pt' if args.composition else 'research/results/motor.pt'))
assert all(torch.equal(v,initial[k]) for k,v in net.state_dict().items() if k not in ['gain','leak','bias'])
report={'before_rmse':before,'after_rmse':after,'ablated_rmse':ablated,'steps':args.steps,'seconds':time.perf_counter()-start,'history':history,'fixed_interfaces':True,'input':'Neurally generated reference, joint angles and velocities, physical tip error, contact force','output':'Three incremental rotary actuator commands; no IK at inference','scope':'Tethered, reduced 3-DOF foreleg with rigid attached stylus; normalized physical parameters'}
if args.composition:report.update(scope='Positioned and resized compositions with continuous physical travel, contact and lifts',placement='Explicit affine transform of the trained canonical shape output',demonstrations=len(rollout_x))
(ROOT/('research/results/composition-motor-training.json' if args.composition else 'research/results/motor-training.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
