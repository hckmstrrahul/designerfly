"""Audit the exact activity payloads sent to the browser against PyTorch."""
import json,unittest
from unittest.mock import patch
import numpy as np
import torch
import server
from core import ROOT,G,Circuit,features
from active_motor import load_network,policy_or,configuration

class TelemetryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):torch.set_num_threads(6)
    def test_motor_payload_matches_actual_last_control_inference(self):
        original=server.motor;inputs=[]
        def capture(x,**kw):inputs.append(x.copy());return original(x,**kw)
        with patch.object(server,'motor',capture):
            created=server.create(server.Start(shape=0))
        try:
            result=server.step(server.Step(session=created['session'],steps=2,wings=True,wing_phase=.25))
            net=Circuit(seed=421,outputs=3);net.load_state_dict(torch.load(ROOT/'research/results/motor.pt',weights_only=False)['state_dict'])
            net=load_network() or net
            with torch.no_grad():actions,state=net(torch.tensor(inputs[-1][None,:]),return_state=True)
            np.testing.assert_allclose(result['state'],state[0].numpy(),atol=2e-5)
            np.testing.assert_allclose(result['frames'][-1]['action'],actions[0].numpy(),atol=2e-5)
            self.assertEqual(result['neural_source'],'motor');self.assertAlmostEqual(result['sample_time'],.02)
            wing_net=Circuit();wing_net.load_state_dict(torch.load(ROOT/'research/results/refined.pt',weights_only=False)['state_dict'])
            with torch.no_grad():point,wing_state=wing_net(torch.tensor(features([1],[.25])),return_state=True)
            np.testing.assert_allclose(result['wing_state'],wing_state[0].numpy(),atol=2e-5)
            self.assertAlmostEqual(result['wing'],float(point[0,0]),places=5)
            stopped=server.step(server.Step(session=created['session'],steps=2,wings=False))
            self.assertIsNone(stopped['wing_state'])
        finally:server.remove(created['session'])
    def test_wing_payload_and_motion_come_from_the_same_neural_inference(self):
        net=Circuit();net.load_state_dict(torch.load(ROOT/'research/results/refined.pt',weights_only=False)['state_dict'])
        for phase in [.13,.51,.87]:
            result=server.wing(phase)
            with torch.no_grad():point,state=net(torch.tensor(features([1],[phase])),return_state=True)
            self.assertAlmostEqual(result['wing'],float(point[0,0]),places=5)
            np.testing.assert_allclose(result['state'],state[0].numpy(),atol=2e-5)
    def test_composition_monitor_shows_the_refined_motor_not_the_shape_planner(self):
        from composition import load_composition_motor
        original=policy_or(load_composition_motor());inputs=[]
        def capture(x,**kw):inputs.append(x.copy());return original(x,**kw)
        with patch.object(server,'composition_motor',capture):
            created=server.create_composition(server.CompositionStart(strokes=[dict(shape=2,x=.2,y=-.25,width=.6,height=.5)]))
        try:
            result=server.step(server.Step(session=created['session'],steps=2,wings=True,wing_phase=.4))
            net=Circuit(seed=421,outputs=3);net.load_state_dict(torch.load(ROOT/'research/results/composition-motor.pt',weights_only=False)['state_dict'])
            net=load_network() or net
            with torch.no_grad():actions,state=net(torch.tensor(inputs[-1][None,:]),return_state=True)
            np.testing.assert_allclose(result['state'],state[0].numpy(),atol=2e-5)
            np.testing.assert_allclose(result['frames'][-1]['action'],actions[0].numpy(),atol=2e-5)
            self.assertEqual(result['neural_source'],'motor')
        finally:server.remove(created['session'])
    def test_display_indices_match_the_neural_graph(self):
        meta=json.loads((ROOT/'public/models/circuit-refined.json').read_text())
        self.assertEqual(meta['bodyIds'],[str(x) for x in G['body_ids']]);self.assertEqual(meta['rows'],G['rows'].tolist());self.assertEqual(meta['col'],G['col'].tolist())
        self.assertEqual(sum(p is not None for p in meta['positions']),758)
        if configuration():
            net=load_network();view=json.loads((ROOT/f"public/models/motor-circuit-{net.neurons}.json").read_text())
            self.assertEqual(view['bodyIds'],[str(x) for x in net.graph['body_ids']])
            self.assertEqual(view['rows'],net.graph['rows'].tolist());self.assertEqual(view['col'],net.graph['col'].tolist())

if __name__=='__main__':unittest.main()
