"""Data isolation tests, not biological validation."""
import unittest
from prepare_receptor_recordings import animal_split

class RecordingSplitTests(unittest.TestCase):
    def test_animals_stay_together_across_files_and_input_order(self):
        animals=[f'fly-{i}' for i in range(15)]
        split=animal_split(animals)
        self.assertEqual(split,animal_split(list(reversed(animals))+animals))
        groups=[set(split[k]) for k in ['train','validation','test']]
        self.assertFalse(groups[0]&groups[1] or groups[0]&groups[2] or groups[1]&groups[2])
        self.assertEqual(set.union(*groups),set(animals))

    def test_insufficient_independent_animals_rejected(self):
        with self.assertRaises(ValueError): animal_split(['a','a','b','c'])

if __name__=='__main__': unittest.main()
