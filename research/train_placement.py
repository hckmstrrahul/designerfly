"""Learn position/size-conditioned strokes on the measured MaleCNS graph."""
import argparse,json,time
import numpy as np
import torch
from core import Circuit,ROOT,target,corners,numpy_infer
from placement import placed_features,placed_targets,sample_placements

p=argparse.ArgumentParser();p.add_argument('--steps',type=int,default=16000);p.add_argument('--refine',action='store_true');args=p.parse_args()
torch.set_num_threads(6);torch.manual_seed(1701);rng=np.random.default_rng(1701)
net=Circuit(seed=123,input_size=20)
# Preserve the trained recurrent circuit and original sensory interface; only
# the four new placement input columns are new, fixed random projections.
old=torch.load(ROOT/'research/results/refined.pt',weights_only=False)['state_dict']
state=net.state_dict()
for key,value in old.items():
    if key!='projection':state[key]=value
state['projection'][:,:16]=old['projection']
net.load_state_dict(state)
if args.refine:net.load_state_dict(torch.load(ROOT/'research/results/placement.pt',weights_only=False)['state_dict'])
initial={k:v.clone() for k,v in net.state_dict().items()}
vrng=np.random.default_rng(1909);vs=vrng.integers(0,3,2048);vt=vrng.random(2048);vp=sample_placements(2048,vrng)
vx=torch.tensor(placed_features(vs,vt,vp));vy=torch.tensor(placed_targets(vs,target(vs,vt),vp))
def score(ablated=False):
    with torch.no_grad():return float((net(vx,ablated=ablated)-vy).square().mean().sqrt())
before=score();opt=torch.optim.Adam(net.parameters(),lr=.003 if args.refine else .005)
start=time.perf_counter();best=1e9;best_state=None;history=[]
for step in range(args.steps):
    n=96;ss=rng.integers(0,3,n);tt=rng.random(n);pp=sample_placements(n,rng)
    for i in range(24):
        if ss[i]!=1:tt[i]=(rng.choice(corners(ss[i]))+rng.normal(0,.002))%1
    eps=.0008
    xx=torch.tensor(placed_features(np.tile(ss,3),np.r_[tt,(tt-eps)%1,(tt+eps)%1],np.tile(pp,(3,1))))
    yy=torch.tensor(placed_targets(ss,target(ss,tt),pp))
    dy=target(ss,tt,True)
    dy[ss==0,1]/=.72;dy[ss==2,1]/=.975;dy*=pp[:,2:]/2
    mask=np.ones(n,dtype=bool)
    for i,s in enumerate(ss):
        if s!=1:mask[i]=np.min(np.abs(((tt[i]-corners(s)+.5)%1)-.5))>.002
    a,b,c=net(xx).chunk(3)
    loss=(a-yy).square().mean()+.12*((((c-b)/(2*eps))[mask]-torch.tensor(dy[mask]))/7).square().mean()
    opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(net.parameters(),.5);opt.step()
    if step in [args.steps//2,args.steps*4//5]:
        for group in opt.param_groups:group['lr']*=.3
    if step%500==0 or step==args.steps-1:
        error=score();rec={'step':step+1,'rmse':error,'seconds':time.perf_counter()-start};history.append(rec);print(json.dumps(rec),flush=True)
        if error<best:best=error;best_state={k:v.clone() for k,v in net.state_dict().items()}
net.load_state_dict(best_state)
fixed=all(torch.equal(v,initial[k]) for k,v in net.state_dict().items() if k not in ['gain','leak','bias'])
assert fixed
after=score();ablated=score(True)
torch.save({'state_dict':net.state_dict()},ROOT/'research/results/placement.pt')
report={'before_rmse':before,'after_rmse':after,'ablated_rmse':ablated,'steps':args.steps,'seconds':time.perf_counter()-start,'fixed_interfaces':fixed,'history':history,'validation':'2048 held-out combinations of shape, phase, center and bounding-box size; not novel shape families','input':'Task, phase harmonics, center x/y and width/height; 20 fixed-interface features','output':'Two placed coordinates. No analytic shape path or affine coordinate transform at live inference.','passed':after<.035 and ablated>after*5}
(ROOT/'research/results/placement-training.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='history'}),flush=True)
