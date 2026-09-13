"""Routing checks independent of the trained spiking checkpoint."""
import unittest
from unittest.mock import patch
import numpy as np
from fastapi import HTTPException
from pydantic import ValidationError
import server

class StatefulMotor:
    def __init__(self):self.calls=0
    def __call__(self,obs,ablated=False):
        self.calls+=1
        return np.zeros(3),np.full(2048,self.calls/100.)

class ControllerAPITests(unittest.TestCase):
    def tearDown(self):
        for key in list(server.sessions):server.remove(key)
    def test_default_remains_trained_and_invalid_names_rejected(self):
        self.assertEqual(server.Start(shape=0).controller,'trained')
        with self.assertRaises(ValidationError):server.Start(shape=0,controller='unknown')
    def test_unvalidated_spiking_is_not_silently_replaced(self):
        with patch.object(server,'spiking_status',return_value={'available':False}):
            with self.assertRaises(HTTPException) as caught:server.create(server.Start(shape=0,controller='spiking'))
        self.assertEqual(caught.exception.status_code,503)
    def test_session_state_is_isolated_and_batched_steps_publish_actual_source(self):
        with patch.object(server,'session_motor',side_effect=lambda kind,fallback:StatefulMotor()):
            a=server.create(server.Start(shape=0,controller='spiking'))
            b=server.create(server.Start(shape=0,controller='spiking'))
        result=server.step(server.Step(session=a['session'],steps=3))
        self.assertEqual(result['neural_source'],'spiking')
        self.assertEqual(len(result['state']),2048)
        self.assertEqual(server.sessions[a['session']][0].motor.calls,3)
        self.assertEqual(server.sessions[b['session']][0].motor.calls,0)
        server.step(server.Step(session=a['session'],steps=2))
        self.assertEqual(server.sessions[a['session']][0].motor.calls,5)
    def test_composition_uses_requested_controller_and_delete_expires_it(self):
        with patch.object(server,'session_motor',return_value=StatefulMotor()):
            a=server.create_composition(server.CompositionStart(controller='spiking',strokes=[dict(shape=0,x=0,y=0,width=.4,height=.4)]))
        self.assertEqual(server.step(server.Step(session=a['session']))['neural_source'],'spiking')
        server.remove(a['session'])
        with self.assertRaises(HTTPException):server.step(server.Step(session=a['session']))

    def test_playback_matches_sequential_steps_and_neural_timestamps(self):
        with patch.object(server,'session_motor',side_effect=lambda kind,fallback:StatefulMotor()):
            a=server.create(server.Start(shape=0));b=server.create(server.Start(shape=0))
        batch=server.playback(server.Playback(session=a['session'],steps=2,count=4,wings=True))['samples']
        self.assertEqual(len(batch),4)
        for index,sample in enumerate(batch):
            expected=server.step(server.Step(session=b['session'],steps=2,wings=True,wing_phase=sample['wing_phase']))
            self.assertEqual(sample['frames'],expected['frames'])
            self.assertEqual(sample['state'],expected['state'])
            self.assertEqual(sample['sample_time'],expected['sample_time'])
            self.assertEqual(sample['wing_state'],expected['wing_state'])
            self.assertAlmostEqual(sample['wing_time'],(index+1)*.04)
        with self.assertRaises(ValidationError):server.Playback(count=31)
    def test_wing_playback_and_completed_drawing_are_bounded(self):
        samples=server.playback(server.Playback(wings=True,count=3,steps=12))['samples']
        self.assertEqual(len(samples),3)
        self.assertAlmostEqual(samples[-1]['wing_time'],.72)
        with patch.object(server,'session_motor',return_value=StatefulMotor()):
            a=server.create(server.Start(shape=0))
        with patch.object(server,'advance_session',return_value={'frames':[{'done':True}]}):
            self.assertEqual(len(server.playback(server.Playback(session=a['session'],count=20))['samples']),1)

    def test_live_switch_preserves_session_body_and_stroke_phase(self):
        with patch.object(server,'session_motor',return_value=StatefulMotor()):
            a=server.create_composition(server.CompositionStart(strokes=[dict(shape=0,x=0,y=0,width=.4,height=.4)]))
        session=server.sessions[a['session']][0]
        session.stage='draw';session.elapsed=.5
        before=session.env.data.qpos.copy();time=session.env.data.time
        replacement=StatefulMotor();replacement.learned_duration_scale=1.6
        with patch.object(server,'session_motor',return_value=replacement):
            server.switch_session_controller(session,'spiking')
        np.testing.assert_array_equal(session.env.data.qpos,before)
        self.assertEqual(session.env.data.time,time)
        self.assertEqual(session.index,0);self.assertAlmostEqual(session.elapsed,.8)
        result=server.playback(server.Playback(session=a['session'],controller='spiking',count=2))
        self.assertEqual(result['samples'][0]['neural_source'],'spiking')
        self.assertEqual(replacement.calls,4)
        with patch.object(server,'session_motor',return_value=StatefulMotor()):
            server.switch_session_controller(session,'trained')
        self.assertEqual(session.controller,'trained')

if __name__=='__main__':unittest.main()
