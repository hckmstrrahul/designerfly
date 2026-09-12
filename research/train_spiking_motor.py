"""Fit interface decoder from offline teacher rollouts; anatomical weights are frozen."""
import os
os.environ.setdefault('OMP_NUM_THREADS','1');os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import json,time,hashlib
import numpy as np
from spiking_motor import SpikingMotor,CHECKPOINT,ROOT
from active_motor import policy_or
from runtime import load_policies
from composition import CompositionSession
rng=np.random.default_rng(9101)
projection=rng.normal(0,9,(256,16));projection[:,9:12]*=4
np.savez(CHECKPOINT,projection=projection,decoder=np.zeros((257,3)),mean=np.zeros(257),scale=np.ones(257),baseline=12.)
planner,fallback=load_policies();teacher=policy_or(fallback)
X=[];Y=[];start=time.time()
for rollout in range(14):
 motor=SpikingMotor()
 def record(obs,ablated=False):
  action,state=teacher(obs)
  X.append(motor.features(obs));Y.append(action)
  return action,state
 strokes=[dict(shape=int(rng.integers(3)),x=float(rng.uniform(-.25,.25)),y=float(rng.uniform(-.25,.25)),width=float(rng.uniform(.3,1.1)),height=float(rng.uniform(.3,1.1))) for _ in range(2)]
 s=CompositionSession(strokes,planner,record)
 for j in range(1800):
  f=s.step()
  if f['done']:break
 print(rollout,len(X),time.time()-start,flush=True)
x=np.array(X);y=np.array(Y);mean=x.mean(0);scale=x.std(0).clip(.01);mean[-1]=0;scale[-1]=1
z=(x-mean)/scale
w=np.linalg.solve(z.T@z+10*np.eye(z.shape[1]),z.T@y)
np.savez(CHECKPOINT,projection=projection,decoder=w,mean=mean,scale=scale,baseline=12.)
error=float(np.mean((z@w-y)**2)**.5)
report={
 'seed':9101,'demonstrations':len(X),'teacher_action_training_rmse':error,
 'checkpoint_sha256':hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest(),
 'graph_sha256':hashlib.sha256((ROOT/'data/circuit-spiking.npz').read_bytes()).hexdigest(),
 'teacher':'active expanded trained rate motor, offline demonstration generation only',
 'training':'ridge regression of motor spike-rate features against teacher actuator commands',
 'rollouts':14,'strokes_per_rollout':2,'ridge_penalty':10.,
 'sensory_encoder':'fixed seeded Gaussian projection of16 reference/joint/velocity/tip-error/contact features onto256 selected sensory neurons; error projection multiplied by4',
 'sensory_current':'clip(40 + projection @ observation,0,150) mV-equivalent drive',
 'tonic_background_mv':12.,'synapse_gain_mv':.15,
 'motor_decoder':'128 motor spike rates filtered100ms, their20ms differences, and constant intercept; standardized then trained257x3 readout',
 'neural_timestep_ms':1,'neural_steps_per_physics_control':20,
 'internal_weights_frozen':True,'input_projection_frozen':True,
 'runtime_teacher':False,'runtime_inverse_kinematics':False,'observation_action_bypass':False,
 'contact_height_offset':-.004,'draw_duration_scale':1.2,'learned_duration_scale':1.6,
 'scope':'Engineered sensory mapping, tonic drive, filtered rate decoder and contact reference calibration; no claim of biological sensory/motor identity, no task-free training claim',
 'discarded_experiment':'Four DAgger rounds degraded contact and were rejected; shipped checkpoint is original deterministic ridge fit',
 'seconds':time.time()-start,
}
(ROOT/'results/spiking-motor-training.json').write_text(json.dumps(report,indent=2)+'\n')
print('RMSE',error,flush=True)
s=CompositionSession([dict(shape=1,x=0.,y=0.,width=1.,height=1.)],planner,SpikingMotor());errors=[];contact=[]
for j in range(1400):
 f=s.step()
 if f['drawing']:errors.append(np.linalg.norm(np.array(f['tip'])[:2]-np.array(f['reference'])[:2]));contact.append(f['contact'])
 if f['done']:break
print('TEST',f['done'],np.mean(errors),np.mean(contact),f['tip'],flush=True)
