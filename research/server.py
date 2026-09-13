"""Local-only physics service. Launch with npm run physics."""
import time,uuid,os,json,hashlib
from typing import Literal
from threading import RLock
import numpy as np
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from core import ROOT,features
from runtime import DrawingSession,load_policies,reports
from composition import CompositionSession,load_placement,load_composition_motor
from active_motor import configuration,policy_or

app=FastAPI()
from starlette.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware,minimum_size=1000,compresslevel=3)
planner,motor=load_policies();motor=policy_or(motor);sessions={};registry_lock=RLock()
# Set ALLOWED_ORIGINS when the frontend connects directly from another host.
from fastapi.middleware.cors import CORSMiddleware
origins=[origin.strip() for origin in os.getenv('ALLOWED_ORIGINS','').split(',') if origin.strip()]
if origins:app.add_middleware(CORSMiddleware,allow_origins=origins,allow_methods=['GET','POST','DELETE'],allow_headers=['Content-Type'],max_age=86400)
from spiking_api import router as spiking_router
app.include_router(spiking_router)
placement_planner=None
composition_motor=None
class Start(BaseModel):
    shape:int=Field(ge=0,le=2)
    controller:Literal['trained','spiking']='trained'
class Stroke(BaseModel):
    shape:int=Field(ge=0,le=2)
    x:float=Field(ge=-1,le=1);y:float=Field(ge=-1,le=1)
    width:float=Field(ge=.02,le=1.72);height:float=Field(ge=.02,le=1.72)
    points:list[tuple[float,float]] | None=Field(default=None,min_length=2,max_length=256)
class CompositionStart(BaseModel):
    strokes:list[Stroke]=Field(min_length=1,max_length=128)
    controller:Literal['trained','spiking']='trained'
class Step(BaseModel):session:str;steps:int=Field(default=2,ge=1,le=12);wings:bool=False;push:bool=False;wing_phase:float=Field(default=0,ge=0,le=1)
def spiking_status():
    path=ROOT/'research/results/spiking-motor-validation.json'
    report=json.loads(path.read_text()) if path.exists() else {}
    checkpoint=ROOT/'research/results/spiking-motor.npz'
    graph=ROOT/'research/data/circuit-spiking.npz'
    matches=checkpoint.exists() and graph.exists() and report.get('checkpoint_sha256')==hashlib.sha256(checkpoint.read_bytes()).hexdigest() and report.get('graph_sha256')==hashlib.sha256(graph.read_bytes()).hexdigest()
    runtime_files=['spiking.py','spiking_motor.py','embodied.py','composition.py','runtime.py']
    code_matches=all((ROOT/'research'/name).exists() and report.get('runtime_sha256',{}).get(name)==hashlib.sha256((ROOT/'research'/name).read_bytes()).hexdigest() for name in runtime_files)
    return {'available':bool(report.get('passed') and matches and code_matches), 'validation':report}

def session_motor(controller,fallback):
    if controller=='trained':return fallback
    if not spiking_status()['available']:raise HTTPException(503,'Spiking motor validation is not complete')
    from spiking_motor import load_spiking_motor
    return load_spiking_motor()

def register_session(session,controller,now):
    session.controller=controller
    session.request_lock=RLock()
    with registry_lock:
        for key,(_,ts) in list(sessions.items()):
            if now-ts>600:del sessions[key]
        if len(sessions)>=8:raise HTTPException(429,'Too many active drawing sessions')
        key=uuid.uuid4().hex;sessions[key]=(session,now)
    return {'session':key,'frame':session.env.snapshot(),'controller':controller}

@app.get('/health')
def health():
    config=configuration();summary=reports()
    if config:
        import json
        summary['active-motor']=json.loads((ROOT/f"research/results/expansion-training-{config['neurons']}.json").read_text())
    return {'ready':True,'region':os.getenv('RAILWAY_REPLICA_REGION','local'),'engine':'MuJoCo','spiking':spiking_status(),'reports':summary,'motor_model':f"/models/motor-circuit-{config['neurons']}.json" if config else None}
@app.post('/session')
def create(request:Start):
    now=time.monotonic()
    return register_session(DrawingSession(request.shape,planner,session_motor(request.controller,motor)),request.controller,now)
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
    return register_session(CompositionSession(strokes,placement_planner,session_motor(request.controller,composition_motor)),request.controller,now)
@app.post('/step')
def step(request:Step):
    with registry_lock:
        if request.session not in sessions:raise HTTPException(404,'Drawing session expired')
        session,_=sessions[request.session]
    with session.request_lock:
        return advance_session(session,request)

def advance_session(session,request):
    with registry_lock:
        if request.session not in sessions:raise HTTPException(404,'Drawing session expired')
        sessions[request.session]=(session,time.monotonic())
    frames=[]
    for i in range(request.steps):
        push=np.array([.8,-.5,.5]) if request.push and i==0 else None
        frames.append(session.step(push=push))
        if frames[-1].get('done'):break
    wing=0.;wing_state=None
    if request.wings:
        out,rate=planner(features([1],[request.wing_phase])[0]);wing=float(out[0]);wing_state=rate.tolist()
    return {'frames':frames,'state':session.last_state.tolist(),'wing':wing,'wing_state':wing_state,'neural_source':'spiking' if session.controller=='spiking' else 'motor','sample_time':session.env.data.time-.02}
class Playback(BaseModel):
    session: str | None = None
    steps: int = Field(default=2,ge=1,le=12)
    count: int = Field(default=20,ge=1,le=30)
    wings: bool = False
    wing_time: float = Field(default=0,ge=0,le=1e9)

@app.post('/playback')
def playback(request:Playback):
    # Keep per-session physics ordered, but amortize the network round trip over
    # several display samples. Each sample retains its matching neural state.
    duration=request.steps*.02
    def sample(i,session=None):
        wing_time=request.wing_time+(i+1)*duration
        phase=(wing_time*1.6)%1
        if session is not None:
            value=advance_session(session,Step(session=request.session,steps=request.steps,wings=request.wings,wing_phase=phase))
        else:
            out,state=planner(features([1],[phase])[0])
            value={'frames':[],'state':[],'wing':float(out[0]),'wing_state':state.tolist(),'sample_time':wing_time,'neural_source':'motor'}
        return dict(value,duration=duration,wing_time=wing_time,wing_phase=phase)
    if request.session is None:
        if not request.wings:raise HTTPException(422,'A drawing session or wings is required')
        return {'samples':[sample(i) for i in range(request.count)]}
    with registry_lock:
        if request.session not in sessions:raise HTTPException(404,'Drawing session expired')
        session,_=sessions[request.session]
    with session.request_lock:
        samples=[]
        for i in range(request.count):
            value=sample(i,session);samples.append(value)
            if value['frames'][-1].get('done'):break
        return {'samples':samples}

@app.delete('/session/{key}')
def remove(key:str):
    with registry_lock:
        entry=sessions.get(key)
    if entry:
        with entry[0].request_lock:
            with registry_lock:sessions.pop(key,None)
    return {'ok':True}
@app.get('/wing')
def wing(phase:float=0):
    out,state=planner(features([1],[phase%1])[0]);return {'wing':float(out[0]),'state':state.tolist()}

if __name__=='__main__':
    import uvicorn
    uvicorn.run(app,host=os.getenv('HOST','127.0.0.1'),port=int(os.getenv('PORT','5192')),log_level='warning')
