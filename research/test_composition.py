import unittest
from unittest.mock import patch
import numpy as np
from pydantic import ValidationError
from fastapi import HTTPException
from composition import CompositionSession,load_placement,load_composition_motor

STROKES=[dict(shape=0,x=-.4,y=-.45,width=.7,height=.3),dict(shape=1,x=.43,y=.4,width=.4,height=.4),dict(shape=2,x=-.25,y=.3,width=.5,height=.5)]

class CompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.planner=load_placement();cls.motor=load_composition_motor()
    def session(self):return CompositionSession(STROKES,type(self).planner,type(self).motor)
    def test_continuous_physics_lifts_and_no_analytic_teacher_during_inference(self):
        s=self.session();last_tip=s.env.tip.copy();seen=set();travel=0
        with patch('embodied.inverse_kinematics',side_effect=AssertionError('IK during inference')),patch('core.target',side_effect=AssertionError('Analytic teacher during inference')),patch.object(s.env,'reset',side_effect=AssertionError('Body reset between strokes')):
            for _ in range(3000):
                f=s.step();self.assertLess(np.linalg.norm(np.array(f['tip'])-last_tip),.025);last_tip=np.array(f['tip'])
                if f['stage']=='travel':travel+=1;self.assertFalse(f['contact']);self.assertFalse(f['drawing'])
                if f['drawing']:seen.add(f['stroke_index'])
                if f['done']:break
        self.assertTrue(s.done);self.assertEqual(seen,{0,1,2});self.assertGreater(travel,100)
    def test_no_paper_cannot_produce_contact_marks(self):
        s=self.session();s.env.model.geom_pos[s.env.paper_id,2]=-4
        for _ in range(500):self.assertFalse(s.step()['contact'])
    def test_request_validation_rejects_unreachable_and_oversized_layouts(self):
        import server
        with self.assertRaises(ValidationError):server.CompositionStart(strokes=[])
        with self.assertRaises(ValidationError):server.CompositionStart(strokes=STROKES*3)
        with self.assertRaises(HTTPException) as caught:server.create_composition(server.CompositionStart(strokes=[dict(shape=0,x=.9,y=0,width=1.,height=.5)]))
        self.assertEqual(caught.exception.status_code,422)

if __name__=='__main__':unittest.main()
