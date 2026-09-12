import unittest
import numpy as np
from spiking import SpikingCircuit

class SpikingTests(unittest.TestCase):
    def graph(self,sign=1):
        return dict(crow=np.array([0,0,1]),col=np.array([0]),counts=np.array([100.]),signs=np.array([sign,0]),sensory=np.array([0]))
    def test_silence_without_stimulus(self):
        c=SpikingCircuit(self.graph())
        self.assertEqual(c.step(100,False)['spikes'],0)
    def test_persistent_state_and_reset(self):
        a,b=SpikingCircuit(self.graph()),SpikingCircuit(self.graph())
        a.step(40);a.step(40);b.step(80)
        np.testing.assert_array_equal(a.voltage,b.voltage)
        np.testing.assert_array_equal(a.rate,b.rate)
        a.reset();self.assertEqual(a.time,0);self.assertFalse(a.rate.any())
    def test_sign_changes_postsynaptic_current_and_weights_stay_fixed(self):
        a,b=SpikingCircuit(self.graph()),SpikingCircuit(self.graph(-1))
        before=a.weights.data.copy();a.step(40);b.step(40)
        self.assertGreater(a.current[1],0);self.assertLess(b.current[1],0)
        np.testing.assert_array_equal(before,a.weights.data)
        self.assertFalse(a.weights.data.flags.writeable)
    def test_refractory_period_limits_spike_frequency(self):
        c=SpikingCircuit(self.graph());c.threshold=.01
        self.assertLessEqual(c.step(100)['spikes'],68)
    def test_real_graph_finite_and_session_isolation(self):
        a,b=SpikingCircuit(),SpikingCircuit()
        result=a.step(240)
        self.assertTrue(np.isfinite(result['state']).all())
        self.assertTrue(result['spikes']>0)
        self.assertEqual(b.time,0);self.assertFalse(b.voltage.any())

if __name__=='__main__':unittest.main()
