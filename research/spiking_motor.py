"""Persistent LIF feedback motor with fixed anatomy and an offline-trained readout.

Observations enter only through a fixed random projection onto the graph's
sensory population. Actuator commands use filtered spikes from its motor
population and their temporal differences; no observation-to-action bypass,
IK, or teacher is called here. Population labels are graph selection labels,
not verified receptor or functional sensory/motor assignments.
"""
from pathlib import Path
import numpy as np
from spiking import SpikingCircuit

ROOT = Path(__file__).resolve().parent
CHECKPOINT = ROOT / 'results/spiking-motor.npz'

class SpikingMotor:
    controller = 'spiking'
    # Engineering calibration to keep an imperfect spiking motor in paper contact.
    contact_height_offset = -.004
    draw_duration_scale = 1.2
    learned_duration_scale = 1.6  # Allow the filtered spiking feedback loop to track fine strokes

    def __init__(self, checkpoint=CHECKPOINT):
        self.circuit = SpikingCircuit()
        with np.load(ROOT / 'data/circuit-spiking.npz') as graph:
            self.motor = graph['motor'].copy()
        with np.load(checkpoint) as data:
            self.projection = data['projection'].copy()
            self.decoder = data['decoder'].copy()
            self.mean = data['mean'].copy()
            self.scale = data['scale'].copy()
            self.baseline = float(data['baseline'])
        width = 2 * len(self.motor) + 1
        if self.projection.shape != (len(self.circuit.sensory), 16) or self.decoder.shape != (width, 3):
            raise ValueError('Spiking motor checkpoint does not match circuit populations')
        if self.mean.shape != (width,) or self.scale.shape != (width,) or np.any(self.scale <= 0):
            raise ValueError('Invalid spiking decoder normalization')
        if not all(np.isfinite(value).all() for value in (self.projection, self.decoder, self.mean, self.scale, self.baseline)):
            raise ValueError('Non-finite spiking motor checkpoint')
        self.previous = np.zeros(len(self.motor))

    def reset(self):
        self.circuit.reset()
        self.previous[:] = 0

    def features(self, obs, ablated=False):
        obs = np.asarray(obs, dtype=float)
        if obs.shape != (16,) or not np.isfinite(obs).all():
            raise ValueError('Expected sixteen finite feedback observations')
        drive = np.full(self.circuit.n, self.baseline)
        drive[self.circuit.sensory] = np.clip(40 + self.projection @ obs, 0, 150)
        self.circuit.step(20, drive=drive, ablated=ablated)
        rate = self.circuit.rate[self.motor] / 100
        features = np.r_[rate, rate - self.previous, 1.]
        self.previous = rate.copy()
        return features

    def __call__(self, obs, ablated=False):
        features = self.features(obs, ablated)
        action = ((features - self.mean) / self.scale) @ self.decoder
        return np.clip(action, -1, 1), np.minimum(self.circuit.rate / 100, 1)


def load_spiking_motor():
    """A new callable and all-new dynamic state for each physical session."""
    return SpikingMotor()
