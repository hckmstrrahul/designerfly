"""Offline learned trajectories for renderer/body-clearance verification."""
import json
from pathlib import Path
from runtime import DrawingSession,load_policies
planner,motor=load_policies()
frames=[]
for shape in range(3):
    session=DrawingSession(shape,planner,motor)
    frames.append(session.env.snapshot())
    for step in range(700):
        frame=session.step()
        frames.append(frame)
Path('research/results/pose-check.json').write_text(json.dumps(frames))
print(f'Exported {len(frames)} physical poses from three learned trajectories')
