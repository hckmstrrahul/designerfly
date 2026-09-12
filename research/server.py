"""Local-only physics service. Launch with npm run physics."""
import time,uuid
import numpy as np
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from core import ROOT,features
from runtime import DrawingSession,load_policies,reports
from composition import CompositionSession,load_placement,load_composition_motor
from active_motor import configuration,policy_or

app=FastAPI();planner,motor=load_policies();motor=policy_or(motor);sessions={}
placement_planner=None
composition_motor=None
class Start(BaseModel):shape:int=Field(ge=0,le=2)
class Stroke(BaseModel):
    shape:int=Field(ge=0,le=2)
    x:float=Field(ge=-1,le=1);y:float=Field(ge=-1,le=1)
    width:float=Field(ge=.02,le=1.72);height:float=Field(ge=.02,le=1.72)
    points:list[tuple[float,float]] | None=Field(default=None,min_length=2,max_length=256)
class CompositionStart(BaseModel):strokes:list[Stroke]=Field(min_length=1,max_length=96)
class Step(BaseModel):session:str;steps:int=Field(default=2,ge=1,le=8);wings:bool=False;push:bool=False;wing_phase:float=Field(default=0,ge=0,le=1)
@app.get('/health')
def health():
    config=configuration();summary=reports()
    if config:
        import json
        summary['active-motor']=json.loads((ROOT/f"research/results/expansion-training-{config['neurons']}.json").read_text())
    return {'ready':True,'engine':'MuJoCo','reports':summary,'motor_model':f"/models/motor-circuit-{config['neurons']}.json" if config else None}
@app.post('/session')
def create(request:Start):
    now=time.monotonic()
    for key,(_,ts) in list(sessions.items()):
        if now-ts>600:del sessions[key]
    if len(sessions)>=8:raise HTTPException(429,'Too many active drawing sessions')
    key=uuid.uuid4().hex;sessions[key]=(DrawingSession(request.shape,planner,motor),now)
    return {'session':key,'frame':sessions[key][0].env.snapshot()}
@app.post('/composition')
def create_composition(request:CompositionStart):
    global placement_planner,composition_motor
    strokes=[s.model_dump() for s in request.strokes]
    if any(not np.isfinite(v) or abs(v)>.500001 for s in strokes for p in (s.get('points') or []) for v in p):
        raise HTTPException(422,'Path points must be finite local coordinates within the shape')
    if any(abs(s['x'])+s['width']/2>1.000001 or abs(s['y'])+s['height']/2>1.000001 for s in strokes):
        raise HTTPException(422,'Keep shapes inside the trained drawing area')
    if placement_planner is None:placement_planner=load_placement()
    if composition_motor is None:composition_motor=policy_or(load_composition_motor())
    now=time.monotonic()
    for key,(_,ts) in list(sessions.items()):
        if now-ts>600:del sessions[key]
    if len(sessions)>=8:raise HTTPException(429,'Too many active drawing sessions')
    key=uuid.uuid4().hex;sessions[key]=(CompositionSession(strokes,placement_planner,composition_motor),now)
    return {'session':key,'frame':sessions[key][0].env.snapshot()}
@app.post('/step')
def step(request:Step):
    if request.session not in sessions:raise HTTPException(404,'Drawing session expired')
    session,_=sessions[request.session];sessions[request.session]=(session,time.monotonic());frames=[]
    for i in range(request.steps):
        push=np.array([.8,-.5,.5]) if request.push and i==0 else None
        frames.append(session.step(push=push))
        if frames[-1].get('done'):break
    wing=0.;wing_state=None
    if request.wings:
        out,rate=planner(features([1],[request.wing_phase])[0]);wing=float(out[0]);wing_state=rate.tolist()
    return {'frames':frames,'state':session.last_state.tolist(),'wing':wing,'wing_state':wing_state,'neural_source':'motor','sample_time':session.env.data.time-.02}
@app.delete('/session/{key}')
def remove(key:str):sessions.pop(key,None);return {'ok':True}
@app.get('/wing')
def wing(phase:float=0):
    out,state=planner(features([1],[phase%1])[0]);return {'wing':float(out[0]),'state':state.tolist()}

if __name__=='__main__':
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=5192,log_level='warning')
