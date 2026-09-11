"""Batching more fixed physics steps must not change the trajectory or drop ink."""
import unittest
import numpy as np
import server

class SpeedTests(unittest.TestCase):
    def test_same_steps_same_trajectory_at_all_speeds(self):
        traces=[]
        for batch in [2,4,8]:
            created=server.create(server.Start(shape=0));frames=[]
            try:
                for _ in range(96//batch):frames.extend(server.step(server.Step(session=created['session'],steps=batch))['frames'])
            finally:server.remove(created['session'])
            traces.append(frames)
        for frames in traces[1:]:
            self.assertEqual(len(frames),len(traces[0]))
            for a,b in zip(traces[0],frames):
                np.testing.assert_array_equal(a['tip'],b['tip']);np.testing.assert_array_equal(a['q'],b['q'])
                self.assertEqual(a['time'],b['time']);self.assertEqual(a['contact'],b['contact'])
    def test_batch_stops_at_completion(self):
        created=server.create(server.Start(shape=0))
        try:
            for _ in range(100):
                result=server.step(server.Step(session=created['session'],steps=8))
                if result['frames'][-1]['done']:break
            self.assertTrue(result['frames'][-1]['done'])
            self.assertFalse(any(f['done'] for f in result['frames'][:-1]))
        finally:server.remove(created['session'])

if __name__=='__main__':unittest.main()
