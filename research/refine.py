"""Position + derivative training, explicit corner samples, held-out straightness metrics."""
import argparse,json,time
import numpy as np
import torch
from core import ROOT,Circuit,features,target,corners

p=argparse.ArgumentParser();p.add_argument('--steps',type=int,default=6000);args=p.parse_args()
torch.set_num_threads(6);torch.manual_seed(812);rng=np.random.default_rng(812)
model=Circuit();checkpoint=torch.load(ROOT/'research/results/checkpoint-123.pt',weights_only=False)
model.load_state_dict(checkpoint['state_dict']);initial={k:v.clone() for k,v in model.state_dict().items()}
shapes=np.repeat(np.arange(3),997);phases=np.tile((np.arange(997)+.371)/997,3)
vx=torch.tensor(features(shapes,phases));vy=target(shapes,phases)
def evaluate():
    with torch.no_grad():pred=model(vx).numpy()
    result={};e=pred-vy
    for s,name in enumerate(['rectangle','circle','triangle']):
        es=e[shapes==s];result[name]={'rmse':float(np.sqrt(np.mean(es**2))),'max_point_error':float(np.max(np.linalg.norm(es,axis=1)))}
        if s!=1:
            cc=corners(s);tt=phases[shapes==s];away=np.min(np.abs(((tt[:,None]-cc+.5)%1)-.5),axis=1)>.012
            tangent=target(np.full(997,s),tt,True);normal=np.c_[-tangent[:,1],tangent[:,0]];normal/=np.linalg.norm(normal,axis=1,keepdims=True)
            result[name]['max_edge_deviation']=float(np.max(np.abs(np.sum(es[away]*normal[away],axis=1))))
            with torch.no_grad():cp=model(torch.tensor(features(np.full(len(cc),s),cc))).numpy()
            result[name]['max_corner_error']=float(np.max(np.linalg.norm(cp-target(np.full(len(cc),s),cc),axis=1)))
    return result
before=evaluate();print(json.dumps({'before':before}),flush=True)
opt=torch.optim.Adam(model.parameters(),lr=.003);best=1e9;best_state=None;history=[];start=time.perf_counter()
for step in range(args.steps):
    ss=rng.integers(0,3,96);tt=rng.random(96)
    # A third of the samples concentrate around turns; derivatives are excluded at discontinuities.
    for i in range(32):
        if ss[i]!=1:tt[i]=(rng.choice(corners(ss[i]))+rng.normal(0,.002))%1
    eps=.0007
    xx=torch.tensor(features(np.tile(ss,3),np.r_[tt,(tt-eps)%1,(tt+eps)%1]))
    yy=torch.tensor(target(ss,tt));dy=torch.tensor(target(ss,tt,True))
    pred=model(xx);a,b,c=pred.chunk(3)
    mask=np.ones(96,dtype=bool)
    for i,s in enumerate(ss):
        if s!=1:mask[i]=np.min(np.abs(((tt[i]-corners(s)+.5)%1)-.5))>.002
    tangent=(c-b)/(2*eps);velocity=((tangent[mask]-dy[mask])/7).square().mean()
    loss=(a-yy).square().mean()+.12*velocity
    opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),.5);opt.step()
    if step in [args.steps//2,args.steps*4//5]:
        for g in opt.param_groups:g['lr']*=.3
    if step%400==0 or step==args.steps-1:
        metrics=evaluate();score=sum(v['rmse'] for v in metrics.values())
        if score<best:best=score;best_state={k:v.clone() for k,v in model.state_dict().items()}
        rec={'step':step+1,'loss':float(loss),'metrics':metrics,'seconds':time.perf_counter()-start};history.append(rec);print(json.dumps(rec),flush=True)
model.load_state_dict(best_state);after=evaluate()
assert all(torch.equal(v,initial[k]) for k,v in model.state_dict().items() if k not in ['gain','leak','bias'])
report={'before':before,'after':after,'seconds':time.perf_counter()-start,'steps':args.steps,'validation':'997 off-grid phases per shape; no target path at inference','method':'Position + finite-difference derivative loss; corner oversampling; derivatives excluded across corners','history':history,'passed':after['rectangle']['max_edge_deviation']<before['rectangle']['max_edge_deviation']*.35 and after['rectangle']['rmse']<.01}
torch.save({'state_dict':model.state_dict()},ROOT/'research/results/refined.pt')
(ROOT/'research/results/refinement.json').write_text(json.dumps(report,indent=2))
meta=json.loads((ROOT/'public/models/circuit-123.json').read_text())
meta.update(values=model.effective().detach().tolist(),leak=(.05+.9*torch.sigmoid(model.leak)).detach().tolist(),bias=model.bias.detach().tolist(),refinement=report)
meta['report']['after']['rmse']=float(np.sqrt(np.mean([v['rmse']**2 for v in after.values()])))
(ROOT/'public/models/circuit-refined.json').write_text(json.dumps(meta,separators=(',',':')))
print(json.dumps({'after':after,'passed':report['passed']}),flush=True)
