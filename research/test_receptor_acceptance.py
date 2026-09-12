import unittest
from receptor_acceptance import assess

class AcceptanceTests(unittest.TestCase):
    def test_mean_gain_cannot_hide_large_individual_regression(self):
        baseline={str(i):10. for i in range(8)}
        candidate={str(i):1. for i in range(8)};candidate['7']=15.
        r=assess(candidate,baseline,kind='primary')
        self.assertGreater(r['relative_improvement'],.05)
        self.assertFalse(r['passed']);self.assertFalse(r['checks']['individual_regression'])

    def test_passive_identity_requires_prediction_over_constant(self):
        base={str(i):10. for i in range(13)}
        self.assertFalse(assess(base,base,kind='passive',constant=base)['passed'])
        constant={k:12. for k in base}
        self.assertTrue(assess(base,base,kind='passive',constant=constant)['passed'])

    def test_too_few_animals_is_not_a_pass(self):
        self.assertFalse(assess({'1':1.,'2':1.},{'1':10.,'2':10.},kind='primary')['passed'])

    def test_zero_and_invalid_baselines(self):
        self.assertFalse(assess({'1':0.},{'1':0.},kind='primary')['passed'])
        with self.assertRaises(ValueError):assess({'1':float('nan')},{'1':1.},kind='primary')
        with self.assertRaises(ValueError):assess({'1':1.},{'2':1.},kind='primary')

if __name__=='__main__':unittest.main()
