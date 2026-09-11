"""Behavior checks for the physical runtime, including intervention and contact gating."""
import unittest
from unittest.mock import patch
import numpy as np
from runtime import load_policies,DrawingSession
from embodied import PAPER_Z,TIP_RADIUS,forward

class PhysicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.planner,cls.motor=load_policies()
    def session(self,shape=0):return DrawingSession(shape,type(self).planner,type(self).motor)
    def test_live_step_uses_dynamics_and_does_not_call_ik(self):
        s=self.session();start=s.env.data.qpos.copy();contacts=0
        with patch('embodied.inverse_kinematics',side_effect=AssertionError('IK at inference')):
            for _ in range(150):
                f=s.step();np.testing.assert_allclose(f['tip'],forward(f['q']),atol=1e-8)
                if f['contact']:
                    contacts+=1;self.assertGreater(f['force'],0);self.assertLessEqual(f['tip'][2],PAPER_Z+TIP_RADIUS+1e-7)
        self.assertGreater(contacts,40);self.assertGreater(np.linalg.norm(s.env.data.qpos-start),.1)
    def test_missing_paper_cannot_leave_contact_marks(self):
        s=self.session();s.env.model.geom_pos[s.env.paper_id,2]=-4
        for _ in range(160):
            f=s.step();self.assertFalse(f['contact']);self.assertEqual(f['force'],0)
    def test_feedback_and_circuit_are_causally_needed(self):
        errors=[]
        for condition in ['normal','feedback_removed','core_removed']:
            s=self.session();trial=[]
            for _ in range(200):
                f=s.step(feedback=condition!='feedback_removed',ablated=condition=='core_removed')
                if f['time']>2:trial.append(np.linalg.norm(np.array(f['tip'])[:2]-np.array(f['reference'])[:2]))
            errors.append(np.mean(trial))
        self.assertLess(errors[0],.04)
        self.assertGreater(errors[1],errors[0]*10);self.assertGreater(errors[2],errors[0]*10)

if __name__=='__main__':unittest.main()
