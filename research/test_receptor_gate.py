"""Numerical/causal acceptance tests on SYNTHETIC fixtures, not biological fitting."""
import unittest
import numpy as np
from receptor_gate import PresynapticReleaseGate


class ReceptorGateTests(unittest.TestCase):
    def gate(self, **kwargs):
        # Synthetic labels only: 0/1 act as 9A inputs; 2 hook; 3 claw; 4 club.
        return PresynapticReleaseGate([[3, 1, 0, 0, 0]], [2], **kwargs)

    def test_targeted_causality_preserves_raw_spikes_and_unmapped_controls(self):
        quiet = self.gate().step([0, 0, 1, 1, 1])
        weak = self.gate().step([0, 1, 1, 1, 1])
        strong = self.gate().step([1, 1, 1, 1, 1])
        self.assertEqual(quiet.transmitted_spikes[2], 1.)
        self.assertGreater(weak.transmitted_spikes[2], strong.transmitted_spikes[2])
        np.testing.assert_array_equal(strong.raw_spikes, [1, 1, 1, 1, 1])
        np.testing.assert_array_equal(strong.transmitted_spikes[[0, 1, 3, 4]], [1, 1, 1, 1])
        np.testing.assert_allclose(strong.activation, [1])
        with self.assertRaises(ValueError):
            strong.raw_spikes[2] = 0

    def test_recovery_and_targeted_input_removal(self):
        gate = self.gate()
        for _ in range(50):
            suppressed = gate.step([1, 1, 1, 1, 1])
        previous = suppressed.release[2]
        for _ in range(600):
            # Source neurons keep spiking: only their verified gate input is blocked.
            frame = gate.step([1, 1, 1, 1, 1], inputs_enabled=False)
            self.assertGreaterEqual(frame.release[2], previous)
            previous = frame.release[2]
        self.assertAlmostEqual(frame.release[2], 1., places=10)
        self.assertEqual(frame.raw_spikes[0], 1.)

    def test_receptor_blockade_keeps_anatomy_and_latent_activation(self):
        gate = self.gate()
        anatomical = gate.counts.toarray().copy()
        for _ in range(20):
            frame = gate.step([1, 1, 1, 1, 1], rdl_blocked=True)
        np.testing.assert_array_equal(frame.transmitted_spikes, frame.raw_spikes)
        self.assertGreater(frame.activation[0], 1.)
        restored = gate.step([0, 0, 1, 1, 1], rdl_blocked=False)
        self.assertLess(restored.release[2], .5)
        np.testing.assert_array_equal(gate.counts.toarray(), anatomical)

    def test_zero_strength_and_sustained_input_are_bounded(self):
        for beta in (0., 1., 1e308):
            gate = self.gate(beta=beta)
            for _ in range(1000):
                frame = gate.step([1, 1, 1, 1, 1], dt_seconds=.0001)
                self.assertTrue(np.isfinite(frame.release).all())
                self.assertTrue(np.all((frame.release >= 0) & (frame.release <= 1)))
            if beta == 0:
                np.testing.assert_array_equal(frame.release, np.ones(5))
        # Very small nonzero activation must not produce inf/inf NaN.
        gate.activation[:] = 1e-320
        frame = gate.step([0, 0, 1, 0, 0])
        self.assertTrue(np.isfinite(frame.release).all())

    def test_event_time_timestep_refinement_and_closed_form_decay(self):
        def replay(dt):
            gate = self.gate(tau_seconds=.02)
            for step in range(round(.1 / dt)):
                t = (step + 1) * dt
                event = any(abs(t-time) < 1e-10 for time in (.01, .025, .04))
                frame = gate.step([int(event), 0, 1, 0, 0], dt_seconds=dt)
            return frame
        coarse, fine = replay(.001), replay(.00025)
        expected = .75 * sum(np.exp(-(.1-t)/.02) for t in (.01, .025, .04))
        np.testing.assert_allclose(coarse.activation, [expected], rtol=1e-12)
        np.testing.assert_allclose(coarse.activation, fine.activation, rtol=1e-12)
        np.testing.assert_allclose(coarse.release, fine.release, rtol=1e-12)
        self.assertAlmostEqual(coarse.time, fine.time)

    def test_off_restores_baseline_routing_and_clears_gate_state(self):
        gate = self.gate()
        baseline = np.arange(25., dtype=float).reshape(5, 5) - 12
        # Distinct unrelated inhibitory edge remains exactly present.
        routed = gate.somatic_weights(baseline).toarray()
        expected = baseline.copy()
        expected[2, :2] = 0
        np.testing.assert_array_equal(routed, expected)
        np.testing.assert_array_equal(gate.somatic_weights(baseline, enabled=False).toarray(), baseline)
        self.assertEqual(routed[3, 0], baseline[3, 0])
        gate.step([1, 1, 1, 1, 1])
        off = gate.step([1, 1, 1, 1, 1], enabled=False)
        np.testing.assert_array_equal(off.transmitted_spikes, off.raw_spikes)
        np.testing.assert_array_equal(off.activation, [0])
        restarted = gate.step([0, 0, 1, 1, 1])
        np.testing.assert_array_equal(restarted.release, np.ones(5))
        self.assertAlmostEqual(restarted.time, .003)

    def test_reset_determinism_and_empty_gate_rows(self):
        gate = self.gate()
        first = [gate.step([1, 0, 1, 0, 0]).activation.copy() for _ in range(10)]
        gate.reset()
        second = [gate.step([1, 0, 1, 0, 0]).activation.copy() for _ in range(10)]
        np.testing.assert_array_equal(first, second)
        empty = PresynapticReleaseGate(np.zeros((1, 5)), [2])
        frame = empty.step(np.ones(5))
        np.testing.assert_array_equal(frame.release, np.ones(5))

    def test_invalid_mapping_parameters_and_events_fail_closed(self):
        cases = [([[1, -1]], [0]), ([[np.nan, 0]], [0]), ([[1, 0]], [2]),
                 ([[1, 0], [0, 1]], [0, 0]), ([[1, 0]], [.5])]
        for counts, targets in cases:
            with self.subTest(counts=counts, targets=targets), self.assertRaises(ValueError):
                PresynapticReleaseGate(counts, targets)
        for kwargs in ({'beta': -1}, {'tau_seconds': 0}, {'beta': float('inf')}):
            with self.assertRaises(ValueError):
                self.gate(**kwargs)
        gate = self.gate()
        for spikes in ([0, 1], [0, .5, 1, 0, 0], [0, 1, np.nan, 0, 0]):
            with self.assertRaises(ValueError):
                gate.step(spikes)
        for dt in (0, -1, float('nan')):
            with self.assertRaises(ValueError):
                gate.step(np.zeros(5), dt_seconds=dt)


if __name__ == '__main__':
    unittest.main()
