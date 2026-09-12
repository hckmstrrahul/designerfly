"""Held-out physical validation for the anatomical spiking motor.

The output is a deployment gate, not a biological-behavior benchmark. Geometry
is supplied; no inverse kinematics, teacher, or body reset may run during steps.
"""
import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path
from unittest.mock import patch

import numpy as np
from composition import CompositionSession, load_placement
from embodied import forward

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / 'research/results/spiking-motor-validation.json'
RUNTIME_FILES = ('spiking.py', 'spiking_motor.py', 'embodied.py', 'composition.py', 'runtime.py')

def runtime_hashes():
    return {name: hashlib.sha256((ROOT/'research'/name).read_bytes()).hexdigest() for name in RUNTIME_FILES}


def fixtures():
    source = """
    const c = await import('./lib/composition.ts');
    const e = await import('./lib/emoji.ts');
    const f = await import('./lib/freehand.ts');
    console.log(JSON.stringify({
      newspaper: c.UI_EXAMPLE,
      lettering: c.textStudy('NEURAL\\nINK 39?'),
      emoji_love: e.emojiStudy('love'),
      emoji_lightning: e.emojiStudy('lightning'),
      freehand_wave: [f.freehandStroke(Array.from({length:201}, (_,i)=>[-.83+i/200*1.66,.36*Math.sin(i/200*Math.PI*5)+.12*Math.cos(i/200*Math.PI*9)]),1)],
      freehand_corners: [f.freehandStroke([[-.8,-.7],[.7,-.6],[.75,.75],[-.6,.65],[-.8,-.7]],1)],
    }));
    """
    return json.loads(subprocess.check_output(['node', '--experimental-strip-types', '--input-type=module', '-e', source], cwd=ROOT))


def weights_hash(motor):
    weights = motor.circuit.weights
    digest = hashlib.sha256()
    for array in (weights.data, weights.indices, weights.indptr):
        digest.update(array.tobytes())
    return digest.hexdigest()


def trial(strokes, planner, factory, condition='normal', max_steps=50000, shape=None):
    motor = factory()
    before = weights_hash(motor)
    if shape is None:
        session = CompositionSession(strokes, planner, motor)
    else:
        from runtime import DrawingSession
        session = DrawingSession(shape, planner, motor)
    errors, contacts, forces = [], [], []
    stroke_contacts = {}
    travel_contact = 0
    draw_steps = 0
    completed_strokes = set()
    max_tip_step = 0.
    last_tip = session.env.tip.copy()
    started = time.perf_counter()
    with patch('embodied.inverse_kinematics', side_effect=AssertionError('IK called during inference')), patch('core.target', side_effect=AssertionError('Teacher called during inference')), patch.object(session.env, 'reset', side_effect=AssertionError('Body reset between strokes')):
        for index in range(max_steps):
            push = [.7,-.5,.4] if condition == 'disturbed' and 40 <= draw_steps < 50 else None
            frame = session.step(ablated=condition == 'core_removed', feedback=condition != 'feedback_removed', push=push)
            tip = np.asarray(frame['tip'])
            np.testing.assert_allclose(tip, forward(frame['q']), atol=1e-8)
            max_tip_step = max(max_tip_step, float(np.linalg.norm(tip-last_tip)))
            last_tip = tip
            if not np.all(np.isfinite(np.r_[tip, frame['action'], frame['qvel']])):
                raise AssertionError('Nonfinite physical frame')
            if frame.get('stage', 'travel' if frame['time'] < .7 else '') == 'travel':
                travel_contact += int(frame['contact'])
            if frame['drawing']:
                draw_steps += 1
                errors.append(float(np.linalg.norm(tip[:2]-np.asarray(frame['reference'])[:2])))
                contacts.append(bool(frame['contact']))
                forces.append(float(frame['force']))
                stroke_contacts.setdefault(frame.get('stroke_index', 0), []).append(bool(frame['contact']))
                completed_strokes.add(frame.get('stroke_index', 0))
            if frame['done']:
                break
    elapsed = time.perf_counter()-started
    immutable = before == weights_hash(motor) and not motor.circuit.weights.data.flags.writeable
    return {
        'completed': bool(frame['done']), 'steps': index+1, 'draw_steps': draw_steps,
        'stroke_count_seen': len(completed_strokes), 'stroke_count_requested': len(strokes) if shape is None else 1,
        'rmse': float(np.sqrt(np.mean(np.square(errors)))) if errors else None,
        'contact_fraction': float(np.mean(contacts)) if contacts else 0.,
        'stroke_contact_fractions': {str(k):float(np.mean(v)) for k,v in stroke_contacts.items()},
        'minimum_stroke_contact_fraction': min((float(np.mean(v)) for v in stroke_contacts.values()), default=0.),
        'max_draw_contact_force': max(forces, default=0.),
        'mean_draw_contact_force': float(np.mean(forces)) if forces else 0.,
        'travel_contact_frames': travel_contact, 'max_tip_step': max_tip_step,
        'weights_frozen': immutable, 'weights_sha256': before,
        'neural_seconds': float(motor.circuit.time), 'physics_seconds': float(session.env.data.time),
        'wall_seconds': elapsed, 'control_steps_per_wall_second': (index+1)/elapsed,
        'mean_hz_final': float(motor.circuit.rate.mean()),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', type=Path, default=ROOT/'research/results/spiking-motor.npz')
    parser.add_argument('--output', type=Path, default=RESULT)
    parser.add_argument('--smoke', action='store_true', help='One fixture only; never writes the production gate')
    args = parser.parse_args()
    from spiking_motor import SpikingMotor
    def load_spiking_motor():
        return SpikingMotor(checkpoint=args.checkpoint)
    checkpoint = args.checkpoint
    initial_runtime_hashes = runtime_hashes()
    initial_checkpoint_hash = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    initial_graph_hash = hashlib.sha256((ROOT/'research/data/circuit-spiking.npz').read_bytes()).hexdigest()
    planner = load_placement()
    cases = fixtures()
    if args.smoke:
        cases = {'freehand_corners': cases['freehand_corners']}
    results = {}
    for name, strokes in cases.items():
        results[name] = trial(strokes, planner, load_spiking_motor)
        print(name, json.dumps(results[name]), flush=True)
    if not args.smoke:
        for shape in range(3):
            name = f'learned_shape_{shape}'
            results[name] = trial([], planner, load_spiking_motor, shape=shape)
            print(name, json.dumps(results[name]), flush=True)
    control_strokes = fixtures()['freehand_corners']
    controls = {}
    for condition in ('normal', 'disturbed', 'feedback_removed', 'core_removed'):
        controls[condition] = trial(control_strokes, planner, load_spiking_motor, condition, max_steps=3000)
        print(condition, json.dumps(controls[condition]), flush=True)
    checks = {
        'runtime_unchanged_during_validation': initial_runtime_hashes == runtime_hashes(),
        'all_strokes_leave_contact_marks': all(r['minimum_stroke_contact_fraction'] > 0 for r in results.values()),
        'checkpoint_unchanged_during_validation': initial_checkpoint_hash == hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
        'graph_unchanged_during_validation': initial_graph_hash == hashlib.sha256((ROOT/'research/data/circuit-spiking.npz').read_bytes()).hexdigest(),
        'all_completed': all(r['completed'] and r['stroke_count_seen'] == r['stroke_count_requested'] for r in results.values()),
        'tracking_rmse_below_035': all(r['rmse'] is not None and r['rmse'] < .035 for r in results.values()),
        'drawing_contact_above_95_percent': all(r['contact_fraction'] > .95 for r in results.values()),
        'travel_pen_lifts': all(r['travel_contact_frames'] == 0 for r in results.values()),
        'fixed_anatomical_weights': all(r['weights_frozen'] for r in [*results.values(), *controls.values()]),
        'neural_physics_clock_alignment': all(abs(r['neural_seconds']-r['physics_seconds']) < 1e-5 for r in results.values()),
        'disturbance_completion': controls['disturbed']['completed'] and controls['disturbed']['rmse'] < .05 and controls['disturbed']['contact_fraction'] > .9,
        'feedback_causally_needed': controls['feedback_removed']['rmse'] > max(.04, controls['normal']['rmse']*2),
        'spiking_core_causally_needed': controls['core_removed']['rmse'] > max(.04, controls['normal']['rmse']*2),
    }
    report = {'passed': all(checks.values()), 'scope': 'Held-out supplied paths; engineered sensory/motor interfaces; not biological accuracy or drawing without training', 'checks': checks, 'results': results, 'controls': controls}
    if checkpoint.exists():
        report['checkpoint_sha256'] = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    report['runtime_sha256'] = runtime_hashes()
    report['graph_sha256'] = hashlib.sha256((ROOT/'research/data/circuit-spiking.npz').read_bytes()).hexdigest()
    if not args.smoke:
        args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'passed': report['passed'], 'checks': checks}), flush=True)
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
