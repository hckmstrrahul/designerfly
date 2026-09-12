"""Reduced, tethered FlyGym-proportioned foreleg in MuJoCo.

Model length unit is millimetres. Mass, gravity and actuation are normalized
engineering parameters; no biological force/time calibration is claimed.
Three rotary actuators, rigid distal stylus, true unilateral paper contact.
"""
import numpy as np
import mujoco

BASE=np.array([.16,-.514,1.07]); L1=.705; L2=1.36
# Cant the foreleg's bending plane outboard so the femur clears the compound eye.
BASE_ROLL=np.pi/4
BASE_ROT=np.array([[1,0,0],[0,np.cos(BASE_ROLL),-np.sin(BASE_ROLL)],[0,np.sin(BASE_ROLL),np.cos(BASE_ROLL)]])
PAPER_Z=.946; TIP_RADIUS=.009
CENTER=np.array([1.55,0.,PAPER_Z]); SCALE=.40

def paper_xy(point):
    """Editor X-right/Y-down to MuJoCo XY; rendering maps world Z to -Y."""
    return CENTER[:2]+np.asarray(point)*np.array([SCALE,-SCALE])

DT=.001; CONTROL_DT=.02
XML=f'''<mujoco model="DF-02 tethered foreleg">
<compiler angle="radian"/><option timestep="{DT}" gravity="0 0 -9.81" integrator="implicitfast" cone="elliptic" iterations="100" tolerance="1e-10"/>
<default><joint damping=".3" armature=".015" limited="true"/>
<geom contype="0" conaffinity="0" density="100"/>
<position kp="60" kv="3" forcelimited="true" forcerange="-12 12"/></default>
<worldbody>
<geom name="paper" type="box" pos="1.55 0 {PAPER_Z-.025}" size=".535 .535 .025" contype="1" conaffinity="1" friction=".08 .001 .0001" solref=".04 1" solimp=".8 .8 .001 .5 2"/>
<body name="femur" pos="{' '.join(map(str,BASE))}" quat="{np.cos(BASE_ROLL/2)} {np.sin(BASE_ROLL/2)} 0 0">
<joint name="yaw" axis="0 0 1" range="-1.2 1.2"/>
<joint name="pitch" axis="0 1 0" range="-2 1.5"/>
<geom type="capsule" fromto="0 0 0 {L1} 0 0" size=".025" mass=".04"/>
<body name="tibia" pos="{L1} 0 0"><joint name="elbow" axis="0 1 0" range="0.02 2.8"/>
<geom type="capsule" fromto="0 0 0 {L2-.20} 0 0" size=".014" mass=".025"/>
<geom name="stylus" type="capsule" fromto="{L2-.30} 0 0 {L2-.01} 0 0" size=".012" mass=".004"/>
<geom name="tip" type="sphere" pos="{L2} 0 0" size="{TIP_RADIUS}" mass=".001" contype="1" conaffinity="1" friction=".08 .001 .0001" solref=".04 1" solimp=".8 .8 .001 .5 2"/>
<site name="pen" pos="{L2} 0 0" size=".005"/>
</body></body></worldbody>
<actuator><position name="yaw_servo" joint="yaw" ctrlrange="-1.2 1.2"/><position name="pitch_servo" joint="pitch" ctrlrange="-2 1.5"/><position name="elbow_servo" joint="elbow" ctrlrange=".02 2.8"/></actuator>
</mujoco>'''

def inverse_kinematics(point):
    """Offline demonstration generator and reset only. Never used by learned step()."""
    x,y,z=BASE_ROT.T@(np.asarray(point)-BASE); r=np.hypot(x,y)
    elbow=np.arccos(np.clip((r*r+z*z-L1*L1-L2*L2)/(2*L1*L2),-.999,.999))
    pitch=np.arctan2(-z,r)-np.arctan2(L2*np.sin(elbow),L1+L2*np.cos(elbow))
    return np.array([np.arctan2(y,x),pitch,elbow])

def forward(q):
    q=np.asarray(q);yaw,pitch,elbow=np.moveaxis(q,-1,0)
    r=L1*np.cos(pitch)+L2*np.cos(pitch+elbow)
    return BASE+np.stack([r*np.cos(yaw),r*np.sin(yaw),-L1*np.sin(pitch)-L2*np.sin(pitch+elbow)],axis=-1)@BASE_ROT.T

def observation(reference,q,qvel,tip,force):
    """16 features; intended point comes only from refined neural shape generator."""
    reference=np.asarray(reference);q=np.asarray(q);tip=np.asarray(tip)
    return np.r_[(reference-CENTER)/.5,(q-np.array([0.,-.7,1.5]))/1.5,np.asarray(qvel)*.05,(reference-tip)/.25,np.clip(force,0,2)*.1,1.,reference[2]-PAPER_Z,0.].astype(np.float32)

class Foreleg:
    def __init__(self):
        self.model=mujoco.MjModel.from_xml_string(XML);self.data=mujoco.MjData(self.model)
        self.tip_id=mujoco.mj_name2id(self.model,mujoco.mjtObj.mjOBJ_GEOM,'tip')
        self.paper_id=mujoco.mj_name2id(self.model,mujoco.mjtObj.mjOBJ_GEOM,'paper')
        self.reset()
    def reset(self,offset=None):
        mujoco.mj_resetData(self.model,self.data)
        self.filtered_force=0.
        self.data.qpos[:]=inverse_kinematics([1.35,0.,1.14])+(np.zeros(3) if offset is None else offset)
        self.data.ctrl[:]=self.data.qpos;mujoco.mj_forward(self.model,self.data)
    @property
    def tip(self):return self.data.site_xpos[0].copy()
    def contact_force(self):
        force=0.;wrench=np.zeros(6)
        for i,c in enumerate(self.data.contact):
            if {c.geom1,c.geom2}=={self.tip_id,self.paper_id}:
                mujoco.mj_contactForce(self.model,self.data,i,wrench);force+=max(0,float(wrench[0]))
        return force
    def sense(self,reference):
        self.filtered_force=.8*self.filtered_force+.2*self.contact_force()
        return observation(reference,self.data.qpos,self.data.qvel,self.tip,self.filtered_force)
    def step(self,action,push=None):
        # Network outputs incremental servo commands; MuJoCo integrates all movement.
        self.data.ctrl[:]=np.clip(self.data.qpos+.12*np.clip(action,-1,1),self.model.actuator_ctrlrange[:,0],self.model.actuator_ctrlrange[:,1])
        self.data.qfrc_applied[:]=np.zeros(3) if push is None else push
        for _ in range(round(CONTROL_DT/DT)):mujoco.mj_step(self.model,self.data)
        self.data.qfrc_applied[:]=0
        mujoco.mj_forward(self.model,self.data)
        if not np.all(np.isfinite(self.data.qpos)):raise RuntimeError('Non-finite physical state')
    def snapshot(self):
        force=self.contact_force();tip=self.tip
        return {'tip':tip.tolist(),'q':self.data.qpos.tolist(),'qvel':self.data.qvel.tolist(),'force':force,'contact':force>1e-5,'torque':self.data.actuator_force.tolist(),'bodies':{name:{'position':self.data.body(name).xpos.tolist(),'quaternion':self.data.body(name).xquat.tolist()} for name in ['femur','tibia']},'time':float(self.data.time)}

if __name__=='__main__':
    import time,json
    env=Foreleg();goal=CENTER+np.array([0,0,TIP_RADIUS-.007]);start=time.perf_counter()
    for _ in range(1000):env.step((inverse_kinematics(goal)-env.data.qpos)*8-env.data.qvel*.12)
    print(json.dumps({'steps_per_second':1000/(time.perf_counter()-start),'goal':goal.tolist(),'state':env.snapshot()}))
