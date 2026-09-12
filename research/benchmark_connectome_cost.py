"""Local sparse-LIF sizing benchmark, not a cloud bill or validated larger motor."""
import os
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import json,time,platform
from pathlib import Path
import numpy as np
import pyarrow.feather as feather
from spiking import SpikingCircuit
from prepare_spiking import prediction
ROOT=Path(__file__).resolve().parent

def main():
    records={r['body']:r for r in feather.read_table(ROOT/'data/neurotransmitters.feather').to_pylist()}
    results=[]
    for size in [2048,4096]:
        with np.load(ROOT/f'data/circuit-{size}.npz') as file:graph={k:file[k].copy() for k in file.files}
        graph['signs']=np.array([prediction(records.get(int(body)))[2] for body in graph['body_ids']])
        circuit=SpikingCircuit(graph);drive=np.full(size,12.);drive[circuit.sensory]=60.
        circuit.step(200,drive=drive)
        trials=[]
        for repeat in range(5):
            start=time.perf_counter();cpu=time.process_time()
            for _ in range(5):circuit.step(200,drive=drive)
            trials.append({'wall_seconds':time.perf_counter()-start,'cpu_seconds':time.process_time()-cpu})
        matrix_bytes=sum(x.nbytes for x in (circuit.weights.data,circuit.weights.indices,circuit.weights.indptr))
        state_bytes=sum(x.nbytes for x in (circuit.voltage,circuit.current,circuit.refractory,circuit.spikes,circuit.rate))
        results.append({'neurons':size,'anatomical_edges':len(graph['counts']),'nonzero_effective_edges':int(np.count_nonzero(circuit.weights.data)), 'sparse_weights_bytes_per_session':matrix_bytes,'five_state_arrays_bytes_per_session':state_bytes,'median_wall_seconds_per_neural_second':float(np.median([t['wall_seconds'] for t in trials])),'median_cpu_seconds_per_neural_second':float(np.median([t['cpu_seconds'] for t in trials])),'trials':trials})
    report={'platform':platform.platform(),'processor':platform.machine(),'scope':'Local CPU sparse LIF only; constant stimulus, same calibration, 200ms warmup and five 1s trials. Excludes physics, rate policies, HTTP, rendering, imports and controller training. Larger graph not enabled or motor-validated.','results':results}
    (ROOT/'results/connectome-cost-benchmark.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
