import unittest
import numpy as np
from calibrate_receptor_v2 import response,fit,select,metrics,FILES


def stats(x,y):
    x=np.asarray(x,float);y=np.asarray(y,float)
    return {'all':np.array([len(x),x.sum(),y.sum(),x@x,x@y,y@y])}

class ReceptorV2Tests(unittest.TestCase):
    def test_reserved_files_not_loaded(self):
        self.assertEqual(set(FILES.values()),{'hook_flexion_01_magnet.parquet','hook_flexion_01_treadmill_platform.parquet','9A_treadmill_platform.parquet'})
    def test_passive_velocity_response_is_bounded_and_directional(self):
        y=response(np.array([-100.,0.,100.]),'saturating',50.)
        np.testing.assert_allclose(y,[2/3,0,0])
    def test_fit_equal_animal_weight_without_heldout_targets(self):
        s={'1':stats([0,1],[1,3]),'2':stats([0,1]*100,[3,5]*100),'9':stats([0,1],[1e9,2e9])}
        np.testing.assert_allclose(fit(s,['1','2']),[2,2],atol=1e-10)
        s['9']=stats([0,1],[-1e9,-2e9])
        np.testing.assert_allclose(fit(s,['1','2']),[2,2],atol=1e-10)
    def test_inner_selection_excludes_outer_animals(self):
        good={'1':stats([0,1],[0,2]),'2':stats([0,1],[0,2]),'9':stats([0,1],[1e9,2e9])}
        bad={'1':stats([0,0],[0,2]),'2':stats([0,0],[0,2]),'9':stats([0,1],[0,2])}
        selected,_,_,_=select([({'name':'good'},good),({'name':'bad'},bad)],['1','2'])
        self.assertEqual(selected['name'],'good')
        self.assertAlmostEqual(metrics(good['1']['all'],(2,0))['mse'],0)

if __name__=='__main__':unittest.main()
