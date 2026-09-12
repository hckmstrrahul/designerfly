"""Guard missing/uncertain annotation handling and anatomical alignment."""
import json
import unittest
import numpy as np
from prepare_spiking import ROOT, prediction


class AnnotationTests(unittest.TestCase):
    def test_uncertain_predictions_have_no_fast_effect(self):
        self.assertEqual(prediction(None)[2:], (0, 'missing_record'))
        self.assertEqual(prediction({'predicted_nt': 'gaba'})[2:], (0, 'missing_confidence'))
        self.assertEqual(prediction({'predicted_nt': 'gaba', 'predicted_nt_confidence': .49})[2:], (0, 'low_confidence'))
        self.assertEqual(prediction({'predicted_nt': 'serotonin', 'predicted_nt_confidence': .99})[2:], (0, 'unmodeled_transmitter'))
        for value in [float('nan'), float('inf'), -1, 1.1]:
            with self.assertRaises(ValueError):
                prediction({'predicted_nt': 'gaba', 'predicted_nt_confidence': value})

    def test_artifact_preserves_anatomy_and_manifest_alignment(self):
        source = np.load(ROOT/'research/data/circuit-2048.npz')
        signed = np.load(ROOT/'research/data/circuit-spiking.npz')
        for key in source.files:
            np.testing.assert_array_equal(source[key], signed[key])
        report = json.loads((ROOT/'research/results/spiking-manifest.json').read_text())
        audit = report['neuron_audit']
        self.assertEqual(len(audit), len(source['body_ids']))
        np.testing.assert_array_equal([r[0] for r in audit], signed['body_ids'])
        np.testing.assert_array_equal([r[1] for r in audit], signed['nt'])
        np.testing.assert_array_equal([r[2] for r in audit], signed['confidence'])
        np.testing.assert_array_equal([r[3] for r in audit], signed['signs'])


if __name__ == '__main__':
    unittest.main()
