"""Runtime invariants: actual actuation, persistent LIF state and fixed anatomy."""
import unittest
from unittest.mock import patch
import numpy as np
from embodied import CONTROL_DT, Foreleg, forward
from composition import CompositionSession
from validate_spiking_motor import weights_hash

STROKES = [dict(shape=0, x=0., y=0., width=1., height=.6,
                points=[[-.5,-.5],[.5,-.5],[.5,.5],[-.5,.5],[-.5,-.5]])]


class SpikingMotorTests(unittest.TestCase):
    def motor(self):
        from spiking_motor import load_spiking_motor
        return load_spiking_motor()

    def test_state_is_persistent_deterministic_and_session_local(self):
        a, b = self.motor(), self.motor()
        observation = Foreleg().sense([1.6,.1,.95])
        first, first_state = a(observation)
        self.assertAlmostEqual(a.circuit.time, CONTROL_DT)
        self.assertEqual(b.circuit.time, 0)
        self.assertFalse(b.circuit.voltage.any())
        twin, twin_state = b(observation)
        np.testing.assert_allclose(first, twin)
        np.testing.assert_allclose(first_state, twin_state)
        initial_time = a.circuit.time
        a(observation)
        self.assertAlmostEqual(a.circuit.time, initial_time+CONTROL_DT)
        self.assertAlmostEqual(b.circuit.time, CONTROL_DT)
        self.assertFalse(np.shares_memory(a.circuit.voltage, b.circuit.voltage))
        self.assertFalse(np.shares_memory(a.circuit.rate, b.circuit.rate))

    def test_weights_are_fixed_while_feedback_changes_actions(self):
        a, b = self.motor(), self.motor()
        env = Foreleg()
        obs = env.sense([1.6,.1,.95])
        before = weights_hash(a)
        changed = obs.copy()
        changed[9:12] += [.7,-.5,.4]
        original_actions, changed_actions = [], []
        for _ in range(20):
            original_actions.append(a(obs)[0])
            changed_actions.append(b(changed)[0])
        self.assertEqual(before, weights_hash(a))
        self.assertFalse(a.circuit.weights.data.flags.writeable)
        self.assertGreater(np.max(np.abs(np.asarray(original_actions)-changed_actions)), 1e-4)

    def test_returned_spiking_action_actuates_physics_without_ik_or_reset(self):
        motor = self.motor()
        session = CompositionSession(STROKES, None, motor)
        start = session.env.data.qpos.copy()
        with patch('embodied.inverse_kinematics', side_effect=AssertionError('IK at inference')), patch.object(session.env, 'reset', side_effect=AssertionError('Runtime reset')):
            for _ in range(150):
                previous_q = session.env.data.qpos.copy()
                frame = session.step()
                expected_ctrl = np.clip(previous_q+.12*np.clip(frame['action'],-1,1), session.env.model.actuator_ctrlrange[:,0], session.env.model.actuator_ctrlrange[:,1])
                np.testing.assert_allclose(session.env.data.ctrl, expected_ctrl, atol=1e-8)
                np.testing.assert_allclose(frame['tip'], forward(frame['q']), atol=1e-8)
        self.assertGreater(np.linalg.norm(session.env.data.qpos-start), .05)
        self.assertAlmostEqual(motor.circuit.time, session.env.data.time, places=6)

    def test_contact_is_physical_not_synthesized_from_reference(self):
        session = CompositionSession(STROKES, None, self.motor())
        session.env.model.geom_pos[session.env.paper_id,2] = -4
        for _ in range(150):
            frame = session.step()
            self.assertFalse(frame['contact'])
            self.assertEqual(frame['force'], 0)


if __name__ == '__main__':
    unittest.main()
