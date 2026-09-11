"""Independent held-out actuator inputs, sparse/PyTorch parity and refined exports."""
import json
import numpy as np
import torch
from core import ROOT,Circuit,features,target,numpy_infer
from embodied import PAPER_Z,inverse_kinematics,forward,observation

torch.set_num_threads(6)
planner=Circuit();planner.load_state_dict(torch.load(ROOT/'research/results/refined.pt',weights_only=False)['state_dict'])
ss=np.repeat(np.arange(3),997);tt=np.tile((np.arange(997)+.371)/997,3);x=torch.tensor(features(ss,tt));y=torch.tensor(target(ss,tt))
meta=json.loads((ROOT/'public/models/circuit-refined.json').read_text())
with torch.no_grad():
    meta['report']['after']['rmse']=float((planner(x)-y).square().mean().sqrt())
    meta['report']['ablated']['rmse']=float((planner(x,ablated=True)-y).square().mean().sqrt())
    shapes=[0,1,2];phases=[.137,.443,.781];outputs,states=planner(torch.tensor(features(shapes,phases)),return_state=True)
meta['report']['seconds']=meta['refinement']['seconds'];meta['report']['stage']='Derivative and corner refinement of seed 123; before is original training baseline'
(ROOT/'public/models/circuit-refined.json').write_text(json.dumps(meta,separators=(',',':')))
(ROOT/'research/results/parity-refined.json').write_text(json.dumps({'shape':shapes,'phase':phases,'output':outputs.tolist(),'states':states.tolist()}))

motor=Circuit(seed=421,outputs=3);motor.load_state_dict(torch.load(ROOT/'research/results/motor.pt',weights_only=False)['state_dict']);untrained=Circuit(seed=421,outputs=3)
rng=np.random.default_rng(90511);n=2048
refs=np.c_[rng.uniform(1.07,1.97,n),rng.uniform(-.43,.43,n),rng.uniform(PAPER_Z-.04,1.17,n)]
desired=np.array([inverse_kinematics(r) for r in refs]);q=desired+rng.normal(0,.035,(n,3));dq=rng.normal(0,.25,(n,3));tips=forward(q);forces=rng.uniform(0,2,n)
vx=torch.tensor(np.array([observation(r,a,b,c,f) for r,a,b,c,f in zip(refs,q,dq,tips,forces)]));vy=torch.tensor(np.clip((desired-q)*8-dq*.12,-1,1),dtype=torch.float32)
with torch.no_grad():
    scores={'untrained_rmse':float((untrained(vx)-vy).square().mean().sqrt()),'trained_rmse':float((motor(vx)-vy).square().mean().sqrt()),'ablated_rmse':float((motor(vx,ablated=True)-vy).square().mean().sqrt())}
    mx,ms=motor(vx[:8],return_state=True)
np_motor=numpy_infer(motor)
for i in range(8):
    out,state=np_motor(vx[i].numpy());np.testing.assert_allclose(out,mx[i].numpy(),atol=2e-5);np.testing.assert_allclose(state,ms[i].numpy(),atol=2e-5)
record={'samples':n,'seed':90511,'validation':'Fresh actuator demonstration inputs, independent of all training batches and rollout examples; randomized force channel','scores':scores,'sparse_pytorch_parity':True,'fixed_interfaces':all(torch.equal(v,untrained.state_dict()[k]) for k,v in motor.state_dict().items() if k not in ['gain','leak','bias'])}
(ROOT/'research/results/motor-validation.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
