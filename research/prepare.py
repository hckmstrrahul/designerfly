"""Select a task-blind, measured MaleCNS motor subcircuit for browser inference."""
from pathlib import Path
import hashlib,json
import numpy as np
import pyarrow as pa
import pyarrow.feather as feather
from scipy import sparse

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'research/data'
EXPECTED={'annotations.feather':'2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2','weights.feather':'e35da783d1c686b2b58b3b87cd6a403ae43bfcfba8bff28e08ef752c1a56afc1'}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(8*1024*1024):h.update(b)
 return h.hexdigest()
for name,expected in EXPECTED.items():
 actual=sha(DATA/name)
 if actual!=expected:raise ValueError(f'Unexpected source hash for {name}: {actual}')
 print('Verified',name,flush=True)
ann=feather.read_table(DATA/'annotations.feather')
print('Annotation schema:',ann.schema,flush=True)
classes=np.array(ann['superclass'].fill_null('').to_pylist())
print('Classes:',dict(zip(*np.unique(classes,return_counts=True))),flush=True)
traced=np.array(ann['status'].fill_null('').to_pylist())=='Traced'
mask=traced & np.char.startswith(classes.astype(str),'vnc_')
nodes=ann.filter(pa.array(mask)).sort_by([('bodyId','ascending')])
ids=nodes['bodyId'].to_numpy();classes=np.array(nodes['superclass'].to_pylist());n=len(ids)
rows=[];cols=[];weights=[]
with pa.memory_map(str(DATA/'weights.feather'),'r') as source:
 reader=pa.ipc.open_file(source)
 for bi in range(reader.num_record_batches):
  batch=reader.get_batch(bi);pre=batch['body_pre'].to_numpy();post=batch['body_post'].to_numpy()
  a=np.searchsorted(ids,pre);b=np.searchsorted(ids,post)
  keep=(a<n)&(b<n)&(ids[np.minimum(a,n-1)]==pre)&(ids[np.minimum(b,n-1)]==post)
  cols.append(a[keep].astype(np.int32));rows.append(b[keep].astype(np.int32));weights.append(batch['weight'].to_numpy()[keep].astype(np.float32))
mat=sparse.coo_matrix((np.concatenate(weights),(np.concatenate(rows),np.concatenate(cols))),shape=(n,n)).tocsr();mat.sum_duplicates();mat.sort_indices()
print('VNC candidate circuit:',n,'neurons',mat.nnz,'edges',flush=True)
motor=np.flatnonzero(classes=='vnc_motor');sensory=np.flatnonzero(classes=='vnc_sensory');intrinsic=np.flatnonzero(~np.isin(classes,['vnc_motor','vnc_sensory']))
# Selection is based only on measured connectivity, never drawing labels or fitting.
def top(candidates,score,k):
 return candidates[np.argsort(-np.asarray(score).ravel()[candidates],kind='stable')[:k]]
selected_motor=top(motor,np.asarray(mat.sum(axis=1)).ravel(),128)
selected_intrinsic=top(intrinsic,np.asarray(mat[selected_motor].sum(axis=0)).ravel(),640)
selected_sensory=top(sensory,np.asarray(mat[selected_intrinsic].sum(axis=0)).ravel(),256)
selected=np.sort(np.r_[selected_motor,selected_intrinsic,selected_sensory])
sub=mat[selected][:,selected].tocsr();sub.sort_indices();subnodes=nodes.take(pa.array(selected))
sc=np.array(subnodes['superclass'].to_pylist());sid=np.flatnonzero(sc=='vnc_sensory');mid=np.flatnonzero(sc=='vnc_motor')
np.savez(DATA/'circuit.npz',rows=np.repeat(np.arange(len(selected)),np.diff(sub.indptr)).astype(np.int32),col=sub.indices.astype(np.int32),crow=sub.indptr.astype(np.int32),counts=sub.data,body_ids=ids[selected],sensory=sid,motor=mid)
feather.write_feather(subnodes,DATA/'circuit-nodes.feather')
manifest={'dataset':'MaleCNS v1.0','license':'CC-BY-4.0','source':'https://male-cns.janelia.org/download/','source_sha256':EXPECTED,'selection':'Traced vnc_* annotations. Top 128 motors by total incoming count; top 640 other VNC cells by outgoing count to these motors; top 256 sensory cells by outgoing count to those interneurons. Ties follow sorted bodyId. Keep every measured edge between selected IDs.','neurons':len(selected),'edges':sub.nnz,'sensory_neurons':len(sid),'motor_neurons':len(mid),'candidate_vnc_neurons':n,'candidate_vnc_edges':mat.nnz,'direction':'row=postsynaptic, column=presynaptic','circuit_sha256':sha(DATA/'circuit.npz'),'scope':'Selected motor subcircuit, not the whole fly brain. Approximate rate dynamics and engineered input/output mappings.'}
(ROOT/'research/results').mkdir(exist_ok=True)
(ROOT/'research/results/graph-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2),flush=True)
