import unittest
import numpy as np
from calibrate_receptor_recordings import calcium,features,fit_affine,lowpass

class RecordingCalibrationTests(unittest.TestCase):
    def test_causal_filter_and_release_suppression(self):
        impulse=np.zeros(200);impulse[50]=1
        response=calcium(impulse,.003333)
        self.assertTrue(np.all(response[:50]==0))
        self.assertGreater(response[60],0)
        self.assertLess(response[-1],response.max())
        drive=lowpass(np.ones(1000),.003333,.1)
        self.assertGreater(drive[-1],.99)
        self.assertLess(1/(1+2*drive[-1]),.34)

    def test_fitting_ignores_heldout_targets_and_weights_animals_equally(self):
        def segment(animal,part,y):return {'animal':animal,'part':part,'y':np.asarray(y,float),'score':np.ones(len(y),bool)}
        segments=[segment('1','train',[1,3]),segment('2','train',[3,5]*100),segment('3','test',[1e9,2e9])]
        x=[np.array([0.,1.]),np.tile([0.,1.],100),np.array([0.,1.])]
        np.testing.assert_allclose(fit_affine(segments,x),[2,2],atol=1e-10)
        segments[-1]['y'][:]=-1e12
        np.testing.assert_allclose(fit_affine(segments,x),[2,2],atol=1e-10)

    def test_analyze_exclusion_does_not_remove_dynamic_input(self):
        s={'velocity':np.r_[np.full(50,-100.),np.zeros(50)],'move':np.zeros(100),'dt':.003333,'score':np.r_[np.zeros(50,bool),np.ones(50,bool)]}
        predicted=features([s],-50,.1,0)[0]
        self.assertGreater(predicted[50],0)
        s['velocity'][:50]=0
        self.assertEqual(features([s],-50,.1,0)[0][50],0)

if __name__=='__main__':unittest.main()
