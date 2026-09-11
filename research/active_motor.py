"""Load a physically validated expanded motor; historical experiments stay intact."""
import json
import numpy as np
import torch
from core import ROOT,Circuit,numpy_infer

def configuration():
    path=ROOT/'research/results/active-motor.json'
    return json.loads(path.read_text()) if path.exists() else None

def load_network():
    config=configuration()
    if config is None:return None
    size=config['neurons']
    report=json.loads((ROOT/f'research/results/expansion-validation-{size}.json').read_text())
    if not report['passed']:raise ValueError('Expanded motor failed physical acceptance')
    graph=np.load(ROOT/f'research/data/circuit-{size}.npz')
    net=Circuit(seed=421,outputs=3,graph=graph,gain_mode='softplus')
    net.load_state_dict(torch.load(ROOT/f'research/results/expanded-motor-{size}.pt',weights_only=False)['state_dict'])
    return net

def policy_or(fallback):
    net=load_network()
    return numpy_infer(net) if net is not None else fallback
