import unittest
import numpy as np
from scipy.optimize import nnls
from calibrate_receptor_v3 import fit,metrics


def stats(x,y):
    x=np.asarray(x,float);y=np.asarray(y,float)
    return {'all':np.r_[len(y),x.sum(0),y.sum(),(x.T@x).ravel(),x.T@y,y@y]}

class TonicCalibrationTests(unittest.TestCase):
    def test_active_set_matches_centered_nnls(self):
        rng=np.random.default_rng(42);x=rng.normal(size=(300,2));y=x@[-1,2]+rng.normal(size=300)*.1+3
        s={'1':stats(x,y)};a,b=fit(s,['1'])
        expected,_=nnls(x-x.mean(0),y-y.mean())
        np.testing.assert_allclose(a,expected,atol=1e-10)
        self.assertAlmostEqual(b,float(y.mean()-expected@x.mean(0)))
        self.assertGreaterEqual(a.min(),0)
    def test_equal_animal_and_no_heldout_fit(self):
        x=np.array([[0,0],[1,0],[0,1],[1,1]],float)
        s={'1':stats(x,x@[2,3]+1),'2':stats(np.tile(x,(100,1)),np.tile(x@[2,3]+3,100)), '9':stats(x,x@[100,-200])}
        a,b=fit(s,['1','2']);np.testing.assert_allclose(a,[2,3],atol=1e-10);self.assertAlmostEqual(b,2)
        s['9']=stats(x,x@[-1e9,1e9]);a2,b2=fit(s,['1','2']);np.testing.assert_allclose(a2,a);self.assertEqual(b2,b)
    def test_movement_only_cannot_use_phasic_feature(self):
        x=np.array([[0,0],[1,0],[0,1],[1,1]],float);y=x@[2,3]+1
        a,b=fit({'1':stats(x,y)},['1'],movement_only=True)
        self.assertEqual(a[0],0);self.assertAlmostEqual(a[1],3);self.assertAlmostEqual(b,2)
        self.assertGreater(metrics(stats(x,y)['all'],(a,b))['mse'],0)

if __name__=='__main__':unittest.main()
