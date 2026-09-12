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

if __name__=='__main__':unittest.main()
