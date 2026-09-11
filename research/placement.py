"""Task conditioning shared by placement training and live inference.

Placement coordinates use the trained workspace, x/y in [-1, 1]. Width and
height are bounding-box extents. No analytic shape coordinates live here.
"""
import numpy as np
from core import features

def placed_features(shapes, phases, placements):
    return np.c_[features(shapes,phases),np.asarray(placements,dtype=np.float32)].astype(np.float32)

def sample_placements(n,rng):
    sizes=rng.uniform(.24,1.72,(n,2))
    centers=rng.uniform(-1,1,(n,2))*(1-sizes/2)
    return np.c_[centers,sizes].astype(np.float32)

def canonical_to_box(shapes,points):
    # Offline labels only. Live placement network directly emits placed points.
    result=np.asarray(points).copy()
    for i,s in enumerate(shapes):
        if s==0:result[i,1]/=.72
        if s==2:result[i,1]=(result[i,1]+.075)/.975
    return result

def placed_targets(shapes,points,placements):
    p=np.asarray(placements)
    return p[:,:2]+canonical_to_box(shapes,points)*p[:,2:]/2
