import sys,json,time,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
import numpy as np
from composition import CompositionSession,load_placement,load_composition_motor
from active_motor import policy_or
motor=policy_or(load_composition_motor());planner=load_placement()
results={}
fixtures=json.loads(subprocess.check_output(['node','--experimental-strip-types','-e', "import('./lib/composition.ts').then(m=>console.log(JSON.stringify({ui:m.UI_EXAMPLE,text:m.textStudy('HELLO\\nWORLD'),alphabet:m.textStudy('ABCDEFGHIJKLMNOPQRST'),remaining:m.textStudy('UVWXYZ0123456789.!?-')})))"],cwd=ROOT))
for name,strokes in fixtures.items():
 s=CompositionSession(strokes,planner,motor);errors=[];contacts=[];ink=[];start=time.time()
 for i in range(50000):
  f=s.step()
  if f['drawing']:
   errors.append(float(np.linalg.norm(np.asarray(f['tip'])[:2]-np.asarray(f['reference'])[:2])))
   contacts.append(f['contact']);ink.append([f['stroke_index'],*f['tip'][:2],bool(f['contact'])])
  if f['done']:break
 results[name]={'completed':s.done,'steps':i+1,'rmse':float(np.sqrt(np.mean(np.square(errors)))),'contact_fraction':float(np.mean(contacts)),'seconds':time.time()-start,'ink':ink}
 print(name,{k:v for k,v in results[name].items() if k!='ink'},flush=True)
for record in results.values():
 del record['ink']
 assert record['completed'] and record['contact_fraction']>.95 and record['rmse']<.035
(ROOT/'research/results/detailed-strokes-validation.json').write_text(json.dumps({'passed':True,'training':'No new training; supplied geometry executed by the existing active motor','results':results},indent=2))
