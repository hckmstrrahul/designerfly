"""Bounded per-browser circuit probes, hosted by the existing physics service."""
import json, time, uuid
from pathlib import Path
from threading import Lock
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from spiking import SpikingCircuit

router = APIRouter(prefix='/spiking')
probes = {}
lock = Lock()
class Advance(BaseModel):
    session: str
    milliseconds: int = Field(default=40,ge=1,le=240)
    stimulus: bool = True
    reset: bool = False

@router.post('/session')
def create():
    with lock:
        now = time.monotonic()
        for key, (_, touched) in list(probes.items()):
            if now-touched > 600: del probes[key]
        if len(probes) >= 8: raise HTTPException(429,'Too many circuit probes')
        key = uuid.uuid4().hex
        probes[key] = (SpikingCircuit(),now)
        manifest = json.loads((Path(__file__).parent/'results/spiking-manifest.json').read_text())
        return {'session': key, 'manifest': manifest}

@router.post('/step')
def advance(request: Advance):
    with lock:
        if request.session not in probes: raise HTTPException(404,'Circuit probe expired')
        circuit, touched = probes[request.session]
        if time.monotonic()-touched > 600:
            del probes[request.session]
            raise HTTPException(404,'Circuit probe expired')
        if request.reset: circuit.reset()
        result = circuit.step(request.milliseconds,request.stimulus)
        probes[request.session] = (circuit,time.monotonic())
        return result

@router.delete('/session/{key}')
def remove(key: str):
    with lock: probes.pop(key,None)
    return {'ok':True}
