"""Reusable measured circuit; frozen sensory/motor maps, trainable internal parameters."""
from pathlib import Path
import math
import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parent.parent
G = np.load(ROOT / 'research/data/circuit.npz')
N = len(G['crow']) - 1

def features(shape, phase):
    p = np.asarray(phase)
    clock = np.stack([f(2*np.pi*k*p) for k in range(1,7) for f in (np.sin,np.cos)], axis=-1)
    return np.c_[np.eye(3)[np.asarray(shape)], clock, np.ones_like(p)].astype(np.float32)

def target(shapes, phases, derivative=False):
    out=[]
    for shape,t in zip(shapes,phases):
        if shape==1:
            out.append([2*np.pi*np.cos(t*2*np.pi),2*np.pi*np.sin(t*2*np.pi)] if derivative else [np.sin(t*2*np.pi),-np.cos(t*2*np.pi)])
            continue
        points=np.array([[-1,-.72],[1,-.72],[1,.72],[-1,.72]]) if shape==0 else np.array([[0,-1.05],[1,.9],[-1,.9]])
        delta=np.roll(points,-1,axis=0)-points; lengths=np.linalg.norm(delta,axis=1); total=lengths.sum(); d=t*total
        for i,length in enumerate(lengths):
            if d<=length or i==len(lengths)-1:
                out.append(delta[i]/length*total if derivative else points[i]+delta[i]*(d/length)); break
            d-=length
    return np.array(out,dtype=np.float32)

def corners(shape):
    if shape==1:return np.array([])
    pts=np.array([[-1,-.72],[1,-.72],[1,.72],[-1,.72]]) if shape==0 else np.array([[0,-1.05],[1,.9],[-1,.9]])
    lengths=np.linalg.norm(np.roll(pts,-1,axis=0)-pts,axis=1)
    return np.r_[0,np.cumsum(lengths)[:-1]/sum(lengths)]

class Circuit(nn.Module):
    def __init__(self,seed=123,input_size=16,outputs=2,graph=None,gain_mode='bounded'):
        super().__init__(); rng=np.random.default_rng(seed)
        G = graph if graph is not None else globals()['G']; N = len(G['crow']) - 1
        self.graph=G; self.neurons=N; self.gain_mode=gain_mode
        rows=torch.tensor(G['rows'],dtype=torch.long); cols=torch.tensor(G['col'],dtype=torch.long)
        self.register_buffer('rows',rows);self.register_buffer('cols',cols)
        counts=torch.tensor(G['counts']); totals=torch.zeros(N).index_add_(0,rows,counts)
        self.register_buffer('base',counts/totals[rows].clamp_min(1))
        self.gain=nn.Parameter(torch.zeros(len(rows))); self.leak=nn.Parameter(torch.zeros(N)); self.bias=nn.Parameter(torch.zeros(N))
        self.register_buffer('sensory',torch.tensor(G['sensory'],dtype=torch.long)); self.register_buffer('motor',torch.tensor(G['motor'],dtype=torch.long))
        self.register_buffer('projection',torch.tensor(rng.normal(0,.42,(len(G['sensory']),input_size)).astype(np.float32)))
        self.register_buffer('decoder',torch.tensor(rng.normal(0,8/math.sqrt(len(G['motor'])),(len(G['motor']),outputs)).astype(np.float32)))
    def effective(self):return self.base*(torch.nn.functional.softplus(self.gain) if self.gain_mode=='softplus' else .05+3.95*torch.sigmoid(self.gain))
    def forward(self,x,return_state=False,ablated=False):
        N=self.neurons
        w=torch.zeros((N,N),device=x.device).index_put((self.rows,self.cols),self.effective())
        if ablated:w=w*0
        drive=torch.zeros((len(x),N),device=x.device);drive[:,self.sensory]=x@self.projection.T
        state=torch.zeros_like(drive);leak=.05+.9*torch.sigmoid(self.leak)
        for _ in range(4):state=(1-leak)*state+leak*torch.tanh(state@w.T+drive+self.bias)
        out=state[:,self.motor]@self.decoder
        return (out,state) if return_state else out

def numpy_infer(model):
    from scipy.sparse import csr_matrix
    G=model.graph; N=model.neurons
    w=csr_matrix((model.effective().detach().numpy(),G['col'],G['crow']),shape=(N,N))
    projection=model.projection.numpy();decoder=model.decoder.numpy();sensory=G['sensory'];motor=G['motor']
    leak=(.05+.9*torch.sigmoid(model.leak)).detach().numpy();bias=model.bias.detach().numpy()
    def run(x,ablated=False):
        drive=np.zeros(N,dtype=np.float32);drive[sensory]=projection@np.asarray(x,dtype=np.float32);state=np.zeros(N,dtype=np.float32)
        for _ in range(4):state=(1-leak)*state+leak*np.tanh((0 if ablated else w@state)+drive+bias)
        return state[motor]@decoder,state
    return run
