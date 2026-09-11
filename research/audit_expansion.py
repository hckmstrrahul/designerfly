"""Measure the added cells' activity and causal contribution without retraining."""
import json
import numpy as np
import torch
from core import ROOT,G,numpy_infer
from active_motor import load_network
from embodied import observation,inverse_kinematics,forward,PAPER_Z,TIP_RADIUS

torch.set_num_threads(6);net=load_network();rng=np.random.default_rng(62811)
refs=np.c_[rng.uniform(1.15,1.95,256),rng.uniform(-.4,.4,256),rng.uniform(PAPER_Z,1.14,256)]
desired=np.array([inverse_kinematics(r) for r in refs]);q=desired+rng.normal(0,.035,(256,3));dq=rng.normal(0,.2,(256,3));tip=forward(q);force=np.maximum(0,(PAPER_Z+TIP_RADIUS-tip[:,2])*4)
x=torch.tensor(np.array([observation(r,a,b,c,f) for r,a,b,c,f in zip(refs,q,dq,tip,force)]))
added=~np.isin(net.graph['body_ids'],G['body_ids']);added_edges=added[net.graph['rows']]|added[net.graph['col']]
pred,state=net(x,return_state=True);pred.square().mean().backward()
record={'neurons':net.neurons,'added_neurons':int(added.sum()),'added_cells_with_nonzero_rate':int((state.detach().numpy()[:,added].max(axis=0)!=0).sum()),'added_edge_gradients_nonzero':int(torch.count_nonzero(net.gain.grad[added_edges])),'added_edges':int(added_edges.sum()),'added_neuron_mean_absolute_rate':float(state[:,added].detach().abs().mean())}
with torch.no_grad():
    net.gain[added_edges]=-100
    removed=net(x)
record['output_change_rmse_when_added_edges_removed']=float((pred.detach()-removed).square().mean().sqrt())
record['interpretation']='Added cells and edges participate, but their contribution is small under this warm start. This is not evidence that expanding neuron count improves drawing.'
(ROOT/'research/results/expansion-contribution.json').write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)
