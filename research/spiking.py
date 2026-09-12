"""Persistent, deterministic LIF circuit with frozen anatomical synapses."""
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix

class SpikingCircuit:
    dt = .001
    tau_membrane = .020
    tau_synapse = .005
    threshold = 15.  # mV above resting potential
    refractory_seconds = .002
    gain = .15  # mV per measured synapse; exploratory global calibration

    def __init__(self, graph=None):
        if graph is None:
            graph = np.load(Path(__file__).resolve().parent/'data/circuit-spiking.npz')
        self.n = len(graph['crow'])-1
        self.sensory = graph['sensory']
        values = graph['counts'].astype(float)*graph['signs'][graph['col']]*self.gain
        self.weights = csr_matrix((values,graph['col'],graph['crow']),shape=(self.n,self.n))
        self.weights.data.flags.writeable = False
        self.reset()

    def reset(self):
        self.voltage = np.zeros(self.n)
        self.current = np.zeros(self.n)
        self.refractory = np.zeros(self.n)
        self.spikes = np.zeros(self.n)
        self.rate = np.zeros(self.n)
        self.time = 0.

    def step(self, milliseconds=40, stimulus=True, drive=None, ablated=False):
        if not isinstance(milliseconds,int) or not 1 <= milliseconds <= 240:
            raise ValueError('Duration must be 1..240 integer milliseconds')
        if drive is None:
            drive = np.zeros(self.n)
            if stimulus: drive[self.sensory] = 20.  # Explicit constant test input, not fly sensation
        else:
            drive = np.asarray(drive, dtype=float)
            if drive.shape != (self.n,) or not np.isfinite(drive).all():
                raise ValueError("Drive must contain one finite current per neuron")
        count = 0
        for _ in range(milliseconds):
            self.current *= np.exp(-self.dt/self.tau_synapse)
            if not ablated: self.current += self.weights @ self.spikes
            blocked = self.refractory > 0
            self.refractory = np.maximum(0,self.refractory-self.dt)
            self.voltage += (drive+self.current-self.voltage)*(1-np.exp(-self.dt/self.tau_membrane))
            self.voltage[blocked] = 0
            self.spikes = ((self.voltage >= self.threshold) & ~blocked).astype(float)
            self.voltage[self.spikes > 0] = 0
            self.refractory[self.spikes > 0] = self.refractory_seconds
            decay = np.exp(-self.dt/.1)
            self.rate = self.rate*decay + self.spikes*(1-decay)/self.dt
            self.time += self.dt
            count += int(self.spikes.sum())
        return {'state': np.minimum(self.rate/100,1).tolist(), 'time': self.time, 'spikes': count, 'mean_hz': float(self.rate.mean()), 'max_hz': float(self.rate.max())}
