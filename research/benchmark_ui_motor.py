"""Quick held-out geometric quality benchmark for a SpikingMotor checkpoint.

Measures actual contact trajectories, not the supplied reference or renderer.
All distances use the physical model's millimetre length units. Roughness is
normal-direction second difference on contiguous contact samples in the
interior of straight reference segments; low roughness alone is not accuracy.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path
from unittest.mock import patch

import numpy as np
from composition import CompositionSession
from embodied import paper_xy
from spiking_motor import SpikingMotor, CHECKPOINT

ROOT = Path(__file__).resolve().parents[1]


def stroke(points, x=0., y=0., width=1., height=1.):
    return dict(shape=0, x=x, y=y, width=width, height=height, points=points)


def cases():
    rounded = []
    radius = .15
    for cx, cy, start in ((.35,-.35,-90),(.35,.35,0),(-.35,.35,90),(-.35,-.35,180)):
        for angle in np.linspace(start, start+90, 9):
            radians = np.deg2rad(angle)
            rounded.append([cx+radius*np.cos(radians), cy+radius*np.sin(radians)])
    rounded.append(rounded[0])
    return {
        'horizontal_rule': stroke([[-.5,0],[.5,0]], x=-.13, y=-.42, width=.79, height=.2),
        'vertical_rule': stroke([[0,-.5],[0,.5]], x=.37, y=.17, width=.2, height=.57),
        'thumbnail_corner': stroke([[-.5,.5],[-.5,-.5],[.5,-.5],[.5,.5]], x=-.30,y=.24,width=.48,height=.35),
        'rounded_card': stroke(rounded,x=.22,y=-.23,width=.56,height=.39),
        'thumbnail_detail': stroke([[-.5,.42],[-.17,-.38],[.12,.12],[.32,-.20],[.5,.42]],x=.24,y=.39,width=.46,height=.24),
    }


def nearest(points, polyline):
    points = np.atleast_2d(points)
    a = polyline[:-1]
    vectors = np.diff(polyline, axis=0)
    squared_lengths = np.sum(vectors*vectors, axis=1)
    parameter = np.sum((points[:,None,:]-a)*vectors, axis=2)/np.maximum(squared_lengths,1e-15)
    clipped = np.clip(parameter,0,1)
    offsets = points[:,None,:]-(a+clipped[...,None]*vectors)
    distances = np.linalg.norm(offsets,axis=2)
    segment = np.argmin(distances,axis=1)
    return distances[np.arange(len(points)),segment], segment, clipped[np.arange(len(points)),segment]


def run(study, checkpoint, max_steps=3000):
    motor = SpikingMotor(checkpoint=checkpoint)
    session = CompositionSession([study],None,motor)
    polyline = paper_xy(np.asarray(study['points'])*[study['width'],study['height']]+[study['x'],study['y']])
    tips, references, contacts, steps = [], [], [], []
    travel_contact = 0
    started = time.perf_counter()
    with patch('embodied.inverse_kinematics',side_effect=AssertionError('IK at inference')):
        for index in range(max_steps):
            frame = session.step()
            if frame['stage']=='travel':
                travel_contact += int(frame['contact'])
            if frame['drawing']:
                tips.append(frame['tip'][:2]); references.append(frame['reference'][:2])
                contacts.append(frame['contact']); steps.append(index)
            if frame['done']:
                break
    tips = np.asarray(tips).reshape(-1,2)
    references = np.asarray(references).reshape(-1,2)
    contacts = np.asarray(contacts,dtype=bool)
    if not len(tips):
        return {'completed':False,'contact_fraction':0.,'error':'No drawing samples'}
    errors = np.linalg.norm(tips-references,axis=1)
    distances,_,_ = nearest(tips,polyline)
    _, segment, parameter = nearest(references,polyline)
    lengths = np.linalg.norm(np.diff(polyline,axis=0),axis=1)
    roughness = []
    for i in range(1,len(tips)-1):
        # Exclude pen lifts, corner transitions and tiny curved arc segments.
        if not all(contacts[i-1:i+2]) or not (segment[i-1]==segment[i]==segment[i+1]):
            continue
        if not (.12 < parameter[i] < .88) or lengths[segment[i]] < .04:
            continue
        vector = polyline[segment[i]+1]-polyline[segment[i]]
        normal = np.array([-vector[1],vector[0]])/np.linalg.norm(vector)
        roughness.append(float(np.dot(tips[i+1]-2*tips[i]+tips[i-1],normal)))
    return {
        'completed':bool(frame['done']), 'steps':index+1,
        'drawing_samples':len(tips),'contact_samples':int(contacts.sum()),
        'contact_fraction':float(contacts.mean()),'travel_contact_frames':travel_contact,
        'tracking_rmse':float(np.sqrt(np.mean(errors**2))),
        'contact_cross_track_rmse':float(np.sqrt(np.mean(distances[contacts]**2))) if contacts.any() else None,
        'contact_cross_track_p95':float(np.quantile(distances[contacts],.95)) if contacts.any() else None,
        'straight_roughness_rms':float(np.sqrt(np.mean(np.square(roughness)))) if roughness else None,
        'straight_roughness_samples':len(roughness),
        'seconds':time.perf_counter()-started,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,default=CHECKPOINT)
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    initial_hash = hashlib.sha256(args.checkpoint.read_bytes()).hexdigest()
    results = {name:run(study,args.checkpoint) for name,study in cases().items()}
    metrics = ('tracking_rmse','contact_cross_track_rmse','contact_cross_track_p95','straight_roughness_rms','contact_fraction')
    aggregate = {metric:float(np.mean([r[metric] for r in results.values() if r.get(metric) is not None])) for metric in metrics}
    report = {
        'checkpoint_sha256':initial_hash,
        'checkpoint_unchanged':initial_hash==hashlib.sha256(args.checkpoint.read_bytes()).hexdigest(),
        'units':'Model millimetres; aggregate metrics are equally weighted per fixture, not pooled samples.',
        'roughness_definition':'RMS normal second differences, contiguous contact samples, interior of straight segments >=0.04 model mm; excludes curvature and corner transitions.',
        'completed':all(r['completed'] for r in results.values()),
        'travel_contact_frames':sum(r['travel_contact_frames'] for r in results.values()),
        'aggregate':aggregate,'results':results,
    }
    report['seconds']=sum(r['seconds'] for r in results.values())
    if args.output:
        args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if not report['checkpoint_unchanged'] or not report['completed']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
