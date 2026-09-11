"""Train only measured-edge gains and neuron biases/leaks; interfaces stay frozen.
Task: shape ID + phase clock -> 2D pen coordinates. No target path at inference.
"""
from pathlib import Path
import argparse, json, math, time, hashlib
import numpy as np
import torch
from torch import nn
import pyarrow.feather as feather

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser();parser.add_argument('--steps',type=int,default=1600);parser.add_argument('--seed',type=int,default=123);parser.add_argument('--device',default='auto');args=parser.parse_args()
torch.set_num_threads(6);torch.manual_seed(args.seed);np.random.seed(args.seed)
device=('mps' if torch.backends.mps.is_available() else 'cpu') if args.device=='auto' else args.device
G=np.load(ROOT/'research/data/circuit.npz');N=len(G['crow'])-1;FEATURES=16

def features(shape,phase):
 # A generic clock encoding, not shape coordinates or a target waypoint.
 one=np.eye(3,dtype=np.float32)[np.asarray(shape)]
 p=np.asarray(phase); clock=np.stack([np.sin(2*np.pi*k*p) if j%2==0 else np.cos(2*np.pi*k*p) for k in range(1,7) for j in range(2)],axis=-1)
 return np.c_[one,clock,np.ones_like(p)].astype(np.float32)

def teacher(shapes,phases):
 out=[]
 for shape,t in zip(shapes,phases):
  if shape==1:out.append([np.sin(t*2*np.pi),-np.cos(t*2*np.pi)]);continue
  points=np.array([[-1,-.72],[1,-.72],[1,.72],[-1,.72]]) if shape==0 else np.array([[0,-1.05],[1,.9],[-1,.9]])
  ends=np.roll(points,-1,axis=0);lengths=np.linalg.norm(ends-points,axis=1);d=t*sum(lengths)
  for i,l in enumerate(lengths):
   if d<=l or i==len(lengths)-1:out.append(points[i]+(ends[i]-points[i])*(d/l));break
   d-=l
 return np.array(out,dtype=np.float32)

class Circuit(nn.Module):
 def __init__(self,seed):
  super().__init__();rng=np.random.default_rng(seed)
  rows=torch.tensor(G['rows'],dtype=torch.long);cols=torch.tensor(G['col'],dtype=torch.long)
  self.register_buffer('rows',rows);self.register_buffer('cols',cols)
  counts=torch.tensor(G['counts']);totals=torch.zeros(N).index_add_(0,rows,counts)
  self.register_buffer('base',counts/totals[rows].clamp_min(1))
  self.gain=nn.Parameter(torch.zeros(len(rows)));self.leak=nn.Parameter(torch.zeros(N));self.bias=nn.Parameter(torch.zeros(N))
  # Frozen random sensory projection and motor projection: no trainable external network.
  self.register_buffer('sensory',torch.tensor(G['sensory'],dtype=torch.long));self.register_buffer('motor',torch.tensor(G['motor'],dtype=torch.long))
  projection=rng.normal(0,.42,(len(G['sensory']),FEATURES)).astype(np.float32)
  self.register_buffer('projection',torch.tensor(projection))
  decoder=rng.normal(0,8/math.sqrt(len(G['motor'])),(len(G['motor']),2)).astype(np.float32)
  self.register_buffer('decoder',torch.tensor(decoder))
 def effective(self):return self.base*(.05+3.95*torch.sigmoid(self.gain))
 def forward(self,x,return_state=False,ablated=False):
  matrix=torch.zeros((N,N),device=x.device).index_put((self.rows,self.cols),self.effective())
  if ablated:matrix=matrix*0
  drive=torch.zeros((len(x),N),device=x.device);drive[:,self.sensory]=x@self.projection.T
  state=torch.zeros_like(drive);leak=.05+.9*torch.sigmoid(self.leak)
  for _ in range(4):state=(1-leak)*state+leak*torch.tanh(state@matrix.T+drive+self.bias)
  result=state[:,self.motor]@self.decoder
  return (result,state) if return_state else result

model=Circuit(args.seed).to(device);initial={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
train_phase=np.tile(np.arange(240)/240,3);train_shapes=np.repeat(np.arange(3),240)
x=torch.tensor(features(train_shapes,train_phase),device=device);y=torch.tensor(teacher(train_shapes,train_phase),device=device)
val_phase=np.tile((np.arange(241)+.5)/241,3);val_shapes=np.repeat(np.arange(3),241)
vx=torch.tensor(features(val_shapes,val_phase),device=device);vy=torch.tensor(teacher(val_shapes,val_phase),device=device)
@torch.no_grad()
def metrics(net,ablated=False):
 pred=net(vx,ablated=ablated);e=(pred-vy).cpu().numpy()
 return {'rmse':float(np.sqrt(np.mean(e**2))),'per_shape_rmse':{name:float(np.sqrt(np.mean(e[val_shapes==i]**2))) for i,name in enumerate(['rectangle','circle','triangle'])}}
before=metrics(model);print(json.dumps({'device':device,'neurons':N,'edges':len(G['rows']),'before':before}),flush=True)
opt=torch.optim.Adam(model.parameters(),lr=.028);history=[];start=time.perf_counter();gradient_audit=None
for step in range(args.steps):
 idx=torch.randint(0,len(x),(128,),device=device);pred=model(x[idx]);loss=(pred-y[idx]).square().mean()
 opt.zero_grad(set_to_none=True);loss.backward()
 if gradient_audit is None:gradient_audit={name:{'nonzero':int(torch.count_nonzero(p.grad).item()),'finite':bool(torch.isfinite(p.grad).all().item())} for name,p in model.named_parameters()}
 torch.nn.utils.clip_grad_norm_(model.parameters(),2);opt.step()
 if step%100==0 or step==args.steps-1:
  rec={'step':step+1,'loss':float(loss.item()),'seconds':time.perf_counter()-start};history.append(rec);print(json.dumps(rec),flush=True)
 if step==args.steps//2:
  for group in opt.param_groups:group['lr']=.012
 if step==args.steps*4//5:
  for group in opt.param_groups:group['lr']=.005

after=metrics(model);ablated=metrics(model,True)
fixed_unchanged=all(torch.equal(v.cpu(),initial[k]) for k,v in model.state_dict().items() if k not in ['gain','leak','bias'])
assert fixed_unchanged
out=ROOT/'research/results';out.mkdir(exist_ok=True)
torch.save({'state_dict':model.cpu().state_dict(),'initial':initial,'args':vars(args)},out/f'checkpoint-{args.seed}.pt')
manifest=json.loads((out/'graph-manifest.json').read_text())
report={'seed':args.seed,'steps':args.steps,'seconds':time.perf_counter()-start,'device':device,'train_samples':len(x),'heldout_samples':len(vx),'validation':'Unseen phase samples inside three trained shape families; no claim of novel shape understanding.','before':before,'after':after,'ablated':ablated,'fixed_interfaces_and_topology_unchanged':fixed_unchanged,'gradient_audit':gradient_audit,'history':history,'passed':after['rmse']<.07 and after['rmse']<before['rmse']*.2,'graph':manifest,'model':'4-step rate network; immutable measured adjacency; trainable positive edge gains, biases and leaks; frozen random sensory and motor interfaces.','inputs':'3-way task code + 6 sine/cosine clock harmonics + constant. No coordinates/waypoints/teacher at inference.','output':'Two learned normalized pen coordinates. Stylus grasp and leg IK are engineered visual mappings; no muscle/contact/biological learning claim.'}
(out/f'training-{args.seed}.json').write_text(json.dumps(report,indent=2));print(json.dumps({'after':after,'ablated':ablated,'passed':report['passed']}),flush=True)
# Browser export with the same graph, interfaces and trained values.
def aslist(t):return t.detach().cpu().numpy().tolist()
meta={'version':1,'neurons':N,'edges':len(G['rows']),'features':FEATURES,'steps':4,'rows':G['rows'].tolist(),'col':G['col'].tolist(),'crow':G['crow'].tolist(),'values':aslist(model.effective()),'leak':aslist(.05+.9*torch.sigmoid(model.leak)),'bias':aslist(model.bias),'sensory':G['sensory'].tolist(),'motor':G['motor'].tolist(),'projection':aslist(model.projection.flatten()),'decoder':aslist(model.decoder.flatten()),'bodyIds':[str(i) for i in G['body_ids']],'report':report}
# Display coordinates are measured soma positions when available, not invented anatomy.
nodes=feather.read_table(ROOT/'research/data/circuit-nodes.feather')
for key in ['somaLocation','soma_position','somaLocationX','soma_location']:
 if key in nodes.column_names:print('Position column',key,flush=True)
meta['nodeClasses']=nodes['superclass'].to_pylist()
meta['positions']=None
for key in ['somaLocation','soma_location']:
 if key in nodes.column_names:meta['positions']=nodes[key].to_pylist();break
public=ROOT/'public/models'
(public/f'circuit-{args.seed}.json').write_text(json.dumps(meta,separators=(',',':')))
# Fixture permits an independent JS-vs-PyTorch inference parity test.
with torch.no_grad():
 fx=features(np.array([0,1,2]),np.array([.137,.413,.829]));fp,fs=model(torch.tensor(fx),True)
 fixture={'shape':[0,1,2],'phase':[.137,.413,.829],'output':aslist(fp),'states':aslist(fs)}
(out/f'parity-{args.seed}.json').write_text(json.dumps(fixture))
