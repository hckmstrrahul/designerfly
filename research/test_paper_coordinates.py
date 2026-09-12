"""The editor and the ink texture must have the same handedness."""
import unittest
import numpy as np
from embodied import paper_xy

class PaperCoordinates(unittest.TestCase):
    def test_editor_points_round_trip_through_physics_and_paper_texture(self):
        # PlaneGeometry rotates -pi/2 around X: canvas down is world +Z.
        # The scene maps MuJoCo Y to world -Z. Verify an asymmetric F outline,
        # including its baseline, rather than a symmetric circle or rectangle.
        outline=np.array([[-.6,.7],[-.6,-.7],[.5,-.7],[-.6,-.7],[-.6,0],[.2,0]])
        for editor in outline:
            physical=paper_xy(editor)
            canvas=np.array([(physical[0]-1.55)/1.15,-physical[1]/1.15])+.5
            expected=editor*.44/1.15+.5
            np.testing.assert_allclose(canvas,expected,atol=1e-12)

if __name__=='__main__':unittest.main()
