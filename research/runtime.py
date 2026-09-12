"""Live neural planner -> neural feedback controller -> MuJoCo. No teacher or IK in step."""
import json
import numpy as np
import torch
from core import ROOT,Circuit,features,numpy_infer
from embodied import Foreleg,CENTER,SCALE,PAPER_Z,TIP_RADIUS,paper_xy

def load_policies():
    planner=Circuit();planner.load_state_dict(torch.load(ROOT/'research/results/refined.pt',weights_only=False)['state_dict'])
    motor=Circuit(seed=421,outputs=3);motor.load_state_dict(torch.load(ROOT/'research/results/motor.pt',weights_only=False)['state_dict'])
    return numpy_infer(planner),numpy_infer(motor)

class DrawingSession:
    def __init__(self,shape,planner,motor,offset=None):
        self.composition=None
        if getattr(motor,'controller',None)=='spiking':
            # The persistent motor needs the same explicit travel/settle sequence
            # as multi-stroke work; do not declare lowering to be drawing.
            from composition import CompositionSession
            self.composition=CompositionSession([dict(shape=shape,x=0.,y=0.,width=1.72,height=1.24 if shape==0 else 1.72)],planner,motor)
            self.shape=shape;self.planner=planner;self.motor=motor;self.env=self.composition.env
            if offset is not None:
                self.env.reset(offset);self.composition.origin=self.env.tip.copy()
                self.composition.travel_duration=self.composition._travel_duration()
            self.last_state=np.zeros(motor.circuit.n);self.last_wing=np.zeros(1024)
            return
        self.shape=shape;self.planner=planner;self.motor=motor;self.env=Foreleg();self.env.reset(offset)
        self.frozen=None;self.last_state=np.zeros(1024);self.last_wing=np.zeros(1024)
    def step(self,ablated=False,feedback=True,push=None):
        if self.composition is not None:
            frame=self.composition.step(ablated=ablated,feedback=feedback,push=push)
            self.last_state=self.composition.last_state
            return frame
        t=self.env.data.time;phase=np.clip((t-1.2)/12,0,1)
        planned,planner_state=self.planner(features([self.shape],[phase])[0])
        down=PAPER_Z+.004+getattr(self.motor,'contact_height_offset',0.)
        height=1.12 if t<.7 else (1.12+(down-1.12)*min(1,(t-.7)/.5))
        if t>13.5:height=down+min(.20,(t-13.5)*.6)
        reference=np.r_[paper_xy(planned),height]
        obs=self.env.sense(reference)
        if self.frozen is None:self.frozen=obs.copy()
        if not feedback:
            # Retain changing intended point, remove joint/tip/contact feedback.
            obs[3:13]=self.frozen[3:13]
        action,state=self.motor(obs,ablated=ablated);self.last_state=state
        self.env.step(action,push)
        frame=self.env.snapshot();frame.update(phase=float(phase),reference=reference.tolist(),point=planned.tolist(),action=action.tolist(),done=bool(t>=13.9),drawing=bool(.7<t<13.5))
        return frame

def reports():
    return {name:json.loads((ROOT/f'research/results/{name}.json').read_text()) for name in ['refinement','motor-training','motor-validation','embodied-validation','composition-motor-training','composition-validation'] if (ROOT/f'research/results/{name}.json').exists()}
