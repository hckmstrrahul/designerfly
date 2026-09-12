"""Experimental receptor-supported axonal release inhibition, not a motor policy.

A caller must supply independently verified 9A->hook edges. No neurotransmitter
label or neuron name is interpreted here. This phenomenological model follows
``docs/receptor-mechanism-evidence.md``: receptor evidence motivates reduced
axonal transmission, not a negative somatic current or a change in raw spikes.
Tau and beta are engineering calibration parameters, NOT measured receptor
kinetics. Input events carry unit amplitude, so timestep refinement must retain
the same event times rather than emitting one spike on every smaller timestep.

When enabled, route the listed gate edges through this module instead of the
ordinary somatic pathway using ``somatic_weights``. All other connections must
remain present. This module is intentionally disconnected from the production
motor until mapping, empirical fitting, and motor validation are complete.
"""
from dataclasses import dataclass
import math
import numpy as np
from scipy.sparse import csr_matrix


@dataclass(frozen=True)
class ReleaseGateFrame:
    raw_spikes: np.ndarray
    transmitted_spikes: np.ndarray
    release: np.ndarray
    activation: np.ndarray
    time: float


class PresynapticReleaseGate:
    """Persistent event-driven release gate for explicitly mapped target axons.

    ``counts[j,i]`` is a nonnegative measured count from source neuron i to the
    hook axon ``targets[j]``. Row-normalization is an engineering choice. Input
    events update ``a = exp(-dt/tau) * a + normalized_counts @ raw_spikes``;
    outgoing raw hook events are multiplied by ``1/(1 + beta*a)``.

    ``rdl_blocked`` retains activation/anatomy but makes transmission unity.
    ``inputs_enabled=False`` omits new gate-input events and permits recovery.
    ``enabled=False`` resets activation and restores exact baseline transmission;
    re-enabling starts from this cleared state. Physical time still advances.
    """
    def __init__(self, counts, targets, *, tau_seconds=.020, beta=1.):
        self.counts = csr_matrix(counts, dtype=np.float64, copy=True)
        self.counts.sum_duplicates()
        self.counts.eliminate_zeros()
        self.targets = np.asarray(targets)
        if self.targets.ndim != 1 or self.targets.dtype.kind not in 'iu':
            raise ValueError('Targets must be a one-dimensional integer ID array')
        self.targets = self.targets.astype(np.int64, copy=True)
        rows, self.neurons = self.counts.shape
        if rows != len(self.targets) or self.neurons < 1:
            raise ValueError('Counts must have one row per mapped target and one column per neuron')
        if len(np.unique(self.targets)) != rows or np.any(self.targets < 0) or np.any(self.targets >= self.neurons):
            raise ValueError('Target IDs must be unique indices within the neuron population')
        if not np.isfinite(self.counts.data).all() or np.any(self.counts.data < 0):
            raise ValueError('Verified synapse counts must be finite and nonnegative')
        if not math.isfinite(tau_seconds) or tau_seconds <= 0:
            raise ValueError('tau_seconds must be finite and positive')
        if not math.isfinite(beta) or beta < 0:
            raise ValueError('beta must be finite and nonnegative')
        self.tau_seconds = float(tau_seconds)
        self.beta = float(beta)
        totals = np.asarray(self.counts.sum(axis=1)).ravel()
        if not np.isfinite(totals).all():
            raise ValueError('Synapse count totals overflow')
        self.normalized = self.counts.multiply((1 / np.maximum(totals, 1))[:, None]).tocsr()
        self.counts.data.flags.writeable = False
        self.normalized.data.flags.writeable = False
        self.targets.flags.writeable = False
        self.reset()

    def reset(self):
        self.activation = np.zeros(len(self.targets), dtype=float)
        self.time = 0.

    def somatic_weights(self, baseline, *, enabled=True):
        """Return a copy with ONLY verified gate edges removed when enabled.

        This routing helper never mutates the recorded anatomical matrix. The
        caller must restore its returned baseline copy when disabling the gate.
        Other inhibitory pathways are deliberately untouched.
        """
        weights = csr_matrix(baseline, copy=True)
        if weights.shape != (self.neurons, self.neurons):
            raise ValueError('Expected square baseline matrix for the same neuron population')
        if not enabled:
            return weights
        rows, cols = self.counts.nonzero()
        if len(rows):
            mutable = weights.tolil()
            mutable[self.targets[rows], cols] = 0
            weights = mutable.tocsr()
            weights.eliminate_zeros()
        return weights

    def step(self, raw_spikes, dt_seconds=.001, *, enabled=True, inputs_enabled=True, rdl_blocked=False):
        raw = np.asarray(raw_spikes, dtype=float)
        if raw.shape != (self.neurons,) or not np.isfinite(raw).all() or np.any((raw != 0) & (raw != 1)):
            raise ValueError('Raw spikes must contain one binary event per neuron')
        if not math.isfinite(dt_seconds) or dt_seconds <= 0:
            raise ValueError('dt_seconds must be finite and positive')
        if enabled:
            self.activation *= math.exp(-dt_seconds / self.tau_seconds)
            if inputs_enabled:
                self.activation += self.normalized @ raw
        else:
            self.activation[:] = 0
        release = np.ones(self.neurons)
        if enabled and not rdl_blocked and self.beta:
            # Algebraically equivalent to 1/(1+beta*a), without product overflow.
            large = self.activation > 1
            gated = np.empty(len(self.targets))
            reciprocal = 1 / self.activation[large]
            gated[large] = reciprocal / (reciprocal + self.beta)
            gated[~large] = 1 / (1 + self.beta * self.activation[~large])
            release[self.targets] = gated
        self.time += dt_seconds
        raw = raw.copy()
        transmitted = raw * release
        activation = self.activation.copy()
        for array in (raw, transmitted, release, activation):
            array.flags.writeable = False
        return ReleaseGateFrame(raw, transmitted, release, activation, self.time)
