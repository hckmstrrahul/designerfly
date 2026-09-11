"""Nested VNC expansions. Retain the 1,024 original cells and frozen interfaces.

Add intrinsic cells ranked only by measured incident synapses to the original
circuit, retaining every measured edge among selected cells. No task labels.
"""
import json,hashlib
import numpy as np
import pyarrow as pa
import pyarrow.feather as feather
from scipy import sparse
from core import ROOT,G

data=ROOT/'research/data';out=ROOT/'research/results'
manifest=json.loads((out/'graph-manifest.json').read_text())
for name,expected in manifest['source_sha256'].items():
    with (data/name).open('rb') as f: actual=hashlib.file_digest(f,'sha256').hexdigest()
    assert actual==expected, name
ann=feather.read_table(data/'annotations.feather')
mask=[status=='Traced' and str(c).startswith('vnc_') for status,c in zip(ann['status'].to_pylist(),ann['superclass'].to_pylist())]
nodes=ann.filter(pa.array(mask)).sort_by([('bodyId','ascending')]);ids=nodes['bodyId'].to_numpy();n=len(ids)
rows=[];cols=[];weights=[]
with pa.memory_map(str(data/'weights.feather'),'r') as f:
    reader=pa.ipc.open_file(f)
    for bi in range(reader.num_record_batches):
        b=reader.get_batch(bi);pre=b['body_pre'].to_numpy();post=b['body_post'].to_numpy()
        a=np.searchsorted(ids,pre);c=np.searchsorted(ids,post)
        keep=(a<n)&(c<n)&(ids[np.minimum(a,n-1)]==pre)&(ids[np.minimum(c,n-1)]==post)
        cols.append(a[keep]);rows.append(c[keep]);weights.append(b['weight'].to_numpy()[keep].astype(np.float32))
mat=sparse.coo_matrix((np.concatenate(weights),(np.concatenate(rows),np.concatenate(cols))),shape=(n,n)).tocsr();mat.sum_duplicates();mat.sort_indices()
original=np.searchsorted(ids,G['body_ids']);classes=np.array(nodes['superclass'].to_pylist())
score=np.asarray(mat[original].sum(axis=0)).ravel()+np.asarray(mat[:,original].sum(axis=1)).ravel()
candidates=np.flatnonzero((classes=='vnc_intrinsic')&~np.isin(ids,G['body_ids']))
ranked=candidates[np.argsort(-score[candidates],kind='stable')]
for size in [2048,4096]:
    selected=np.sort(np.r_[original,ranked[:size-len(original)]])
    assert len(selected)==size
    sub=mat[selected][:,selected].tocsr();sub.sort_indices();subnodes=nodes.take(pa.array(selected))
    body=ids[selected];remap=np.searchsorted(body,G['body_ids'])
    np.savez(data/f'circuit-{size}.npz',rows=np.repeat(np.arange(size),np.diff(sub.indptr)).astype(np.int32),col=sub.indices.astype(np.int32),crow=sub.indptr.astype(np.int32),counts=sub.data,body_ids=body,sensory=remap[G['sensory']],motor=remap[G['motor']])
    feather.write_feather(subnodes,data/f'circuit-nodes-{size}.feather')
    record={**manifest,'neurons':size,'edges':sub.nnz,'selection':'Original 1024 cells plus intrinsic VNC neighbors ranked by total measured incoming + outgoing synapses with the original circuit. Ties by bodyId. Frozen original 256 sensory and 128 motor interfaces; all induced measured edges retained.','added_intrinsic':size-1024}
    with (data/f'circuit-{size}.npz').open('rb') as f:record['circuit_sha256']=hashlib.file_digest(f,'sha256').hexdigest()
    (out/f'graph-manifest-{size}.json').write_text(json.dumps(record,indent=2));print(json.dumps({'neurons':size,'edges':sub.nnz}),flush=True)
