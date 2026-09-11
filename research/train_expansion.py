"""Warm-start nested motor expansions with the same frozen input/output maps.

Matched refinement budgets, one seed. This is an engineering comparison, not a
from-scratch neuron scaling law or proof that measured wiring beats random wiring.
"""
import argparse,json,time
import numpy as np
import torch
import pyarrow.feather as feather
from core import ROOT,G,Circuit,numpy_infer
from embodied import observation,inverse_kinematics,forward,PAPER_Z,TIP_RADIUS

p=argparse.ArgumentParser();p.add_argument('--steps',type=int,default=2400);p.add_argument('--sizes',type=int,nargs='+',default=[1024,2048,4096]);args=p.parse_args()
torch.set_num_threads(6);torch.manual_seed(421)
old=Circuit(seed=421,outputs=3);old.load_state_dict(torch.load(ROOT/'research/results/composition-motor.pt',weights_only=False)['state_dict'])
def examples(n,rng):
    refs=np.c_[rng.uniform(1.07,1.97,n),rng.uniform(-.43,.43,n),rng.uniform(PAPER_Z-.04,1.17,n)]
    desired=np.array([inverse_kinematics(r) for r in refs]);scale=np.where(rng.random((n,1))<.9,.035,.14)
    q=desired+rng.normal(0,1,(n,3))*scale;dq=rng.normal(0,.25,(n,3));tip=forward(q);force=np.maximum(0,(PAPER_Z+TIP_RADIUS-tip[:,2])*4)
    x=np.array([observation(r,a,b,c,f) for r,a,b,c,f in zip(refs,q,dq,tip,force)])
    y=np.clip((desired-q)*8-dq*.12,-1,1)
    return torch.tensor(x),torch.tensor(y,dtype=torch.float32)
tx,ty=examples(24000,np.random.default_rng(43101));vx,vy=examples(2048,np.random.default_rng(77943))
records=[]
for size in args.sizes:
    graph=G if size==1024 else np.load(ROOT/f'research/data/circuit-{size}.npz')
    net=Circuit(seed=421,outputs=3,graph=graph,gain_mode='softplus')
    remap=np.searchsorted(graph['body_ids'],G['body_ids'])
    old_edges={(int(remap[r]),int(remap[c])):i for i,(r,c) in enumerate(zip(G['rows'],G['col']))}
    with torch.no_grad():
        net.projection.copy_(old.projection);net.decoder.copy_(old.decoder)
        net.bias[remap]=old.bias;net.leak[remap]=old.leak;net.gain.fill_(-3)
        oldweights=old.effective()
        for i,(r,c) in enumerate(zip(graph['rows'],graph['col'])):
            previous=old_edges.get((int(r),int(c)))
            if previous is not None:
                # Preserve old effective edge weights exactly despite new row sums.
                # Stable inverse softplus; no upper clipping of the old controller.
                v=oldweights[previous]/net.base[i]
                net.gain[i]=v+torch.log(-torch.expm1(-v))
    fixed={k:v.clone() for k,v in net.state_dict().items() if k not in ['gain','leak','bias']}
    def score():
        with torch.no_grad():return float((net(vx)-vy).square().mean().sqrt())
    before=score();best=before;best_state={k:v.clone() for k,v in net.state_dict().items()};opt=torch.optim.Adam(net.parameters(),lr=.002)
    rng=np.random.default_rng(90210);start=time.perf_counter()
    for step in range(args.steps):
        ix=rng.integers(0,len(tx),128);loss=(net(tx[ix])-ty[ix]).square().mean();opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(net.parameters(),1);opt.step()
        if step in [args.steps//2,args.steps*4//5]:
            for group in opt.param_groups:group['lr']*=.3
        if (step+1)%400==0 or step==args.steps-1:
            metric=score()
            if metric<best:best=metric;best_state={k:v.clone() for k,v in net.state_dict().items()}
            print(json.dumps({'neurons':size,'step':step+1,'validation':metric,'seconds':time.perf_counter()-start}),flush=True)
    net.load_state_dict(best_state)
    assert all(torch.equal(v,net.state_dict()[k]) for k,v in fixed.items())
    inference=numpy_infer(net);start_latency=time.perf_counter()
    for i in range(500):inference(vx[i].numpy())
    latency=(time.perf_counter()-start_latency)/500*1000
    with torch.no_grad():
        ablated=float((net(vx,ablated=True)-vy).square().mean().sqrt());actions,states=net(vx[:3],return_state=True)
    for i in range(3):
        a,s=inference(vx[i].numpy());np.testing.assert_allclose(a,actions[i].numpy(),atol=2e-5);np.testing.assert_allclose(s,states[i].numpy(),atol=2e-5)
    record={'neurons':size,'edges':len(graph['rows']),'steps':args.steps,'before_rmse':before,'after_rmse':best,'ablated_rmse':ablated,'seconds':time.perf_counter()-start,'inference_ms':latency,'dense_matrix_mib':size*size*4/1024**2,'fixed_interfaces':True,'runtime_parity':True,'seed':421,'comparison':'Same pretrained 1024 composition motor, nested expansion, same 24000 offline examples and refinement budget; one seed. Validation selects checkpoint; physical acceptance uses separate layouts.'}
    record['gain_mode']='softplus';record['new_edge_initial_gain']=-3
    torch.save({'state_dict':net.state_dict(),'gain_mode':'softplus'},ROOT/f'research/results/expanded-motor-{size}.pt')
    (ROOT/f'research/results/expansion-training-{size}.json').write_text(json.dumps(record,indent=2));records.append(record)
    nodes=feather.read_table(ROOT/('research/data/circuit-nodes.feather' if size==1024 else f'research/data/circuit-nodes-{size}.feather'))
    meta={'neurons':size,'edges':len(graph['rows']),'steps':4,'bodyIds':[str(x) for x in graph['body_ids']],'positions':nodes['somaLocation'].to_pylist(),'nodeClasses':nodes['superclass'].to_pylist(),'rows':graph['rows'].tolist(),'col':graph['col'].tolist(),'report':record}
    (ROOT/f'public/models/motor-circuit-{size}.json').write_text(json.dumps(meta,separators=(',',':')))
    print(json.dumps(record),flush=True)
(ROOT/'research/results/expansion-comparison.json').write_text(json.dumps(records,indent=2))
