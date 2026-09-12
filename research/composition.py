"""Learned placed strokes executed in one continuous physical session.

The sequencer supplies task timing and pen height. It never resets the body
between strokes or calls IK/analytic shape geometry during step().
"""
import numpy as np
import torch
from core import ROOT,Circuit,numpy_infer,features
from embodied import Foreleg,CENTER,PAPER_Z,CONTROL_DT,paper_xy

def load_placement():
    net=Circuit()
    net.load_state_dict(torch.load(ROOT/'research/results/refined.pt',weights_only=False)['state_dict'])
    return numpy_infer(net)

def load_composition_motor():
    net=Circuit(seed=421,outputs=3)
    net.load_state_dict(torch.load(ROOT/'research/results/composition-motor.pt',weights_only=False)['state_dict'])
    return numpy_infer(net)

def place_point(point,stroke):
    """Explicit engineering transform of a learned path; not neural inference."""
    p=np.asarray(point).copy()
    if stroke['shape']==0:p[1]/=.72
    if stroke['shape']==2:p[1]=(p[1]+.075)/.975
    return np.array([stroke['x'],stroke['y']])+p*np.array([stroke['width'],stroke['height']])/2

class CompositionSession:
    def __init__(self,strokes,planner,motor):
        self.strokes=strokes;self.planner=planner;self.motor=motor
        self.env=Foreleg();self.last_state=np.zeros(1024,dtype=np.float32)
        self.index=0;self.stage='travel';self.elapsed=0.;self.done=False
        self.origin=self.env.tip.copy();self.last_reference=self.origin.copy()
        self.travel_duration=self._travel_duration()
    def planned(self,phase):
        s=self.strokes[self.index]
        if s.get('points'):
            points=np.asarray(s['points'])*[s['width'],s['height']]+[s['x'],s['y']]
            distances=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
            # Supplied vector geometry; the trained neural motor still executes every motion.
            distance=phase*distances[-1]
            return np.array([np.interp(distance,distances,points[:,axis]) for axis in range(2)])
        point,_=self.planner(features([s['shape']],[phase])[0])
        return place_point(point,s)
    def _travel_duration(self):
        start=paper_xy(self.planned(0))
        return max(1.,float(np.linalg.norm(start-self.origin[:2]))/.26)
    def step(self,ablated=False,feedback=True,push=None):
        s=self.strokes[self.index];duration=max(3.,6.*max(s['width'],s['height']))
        if s.get('points'):
            length=np.linalg.norm(np.diff(np.asarray(s['points'])*[s['width'],s['height']],axis=0),axis=1).sum()
            duration=max(1.2,float(length)*3.)
        duration*=getattr(self.motor,'draw_duration_scale' if s.get('points') else 'learned_duration_scale',1.)
        phase=float(np.clip(self.elapsed/duration,0,1)) if self.stage=='draw' else (1. if self.stage in ['lift','done'] else 0.)
        point=self.planned(phase);xy=paper_xy(point)
        raised=1.14;down=PAPER_Z+.004+getattr(self.motor,'contact_height_offset',0.)
        if self.stage=='travel':
            t=min(1.,self.elapsed/self.travel_duration);t=t*t*(3-2*t)
            xy=self.origin[:2]*(1-t)+xy*t;z=raised
        elif self.stage=='lower':z=raised+(down-raised)*min(1.,self.elapsed/.6)
        elif self.stage=='draw':z=down
        else:z=down+(raised-down)*min(1.,self.elapsed/.65)
        reference=np.r_[xy,z];obs=self.env.sense(reference)
        if not hasattr(self,'frozen'):self.frozen=obs.copy()
        if not feedback:obs[3:13]=self.frozen[3:13]
        action,self.last_state=self.motor(obs,ablated=ablated);self.env.step(action,push)
        frame=self.env.snapshot()
        frame.update(reference=reference.tolist(),point=point.tolist(),action=action.tolist(),shape=s['shape'],stroke_index=self.index,stroke_count=len(self.strokes),stroke_phase=phase,stage=self.stage,phase=(self.index+phase)/len(self.strokes),drawing=self.stage=='draw',done=self.done)
        self.elapsed+=CONTROL_DT;self.last_reference=reference
        if self.stage=='travel' and self.elapsed>=self.travel_duration+.3:self.stage='lower';self.elapsed=0.
        elif self.stage=='lower' and self.elapsed>=1.:self.stage='draw';self.elapsed=0.
        elif self.stage=='draw' and self.elapsed>duration+.20:self.stage='lift';self.elapsed=0.
        elif self.stage=='lift' and self.elapsed>=.9 and not frame['contact']:
            if self.index+1==len(self.strokes):self.done=True;self.stage='done';frame['done']=True;frame['phase']=1.
            else:
                self.index+=1;self.stage='travel';self.elapsed=0.;self.origin=self.env.tip.copy();self.travel_duration=self._travel_duration()
        return frame
