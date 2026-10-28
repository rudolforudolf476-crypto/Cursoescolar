import unittest
from targeting import select_target


class TargetingTests(unittest.TestCase):
    def test_closest_valid_person_wins(self):
        boxes = [(110, 90, 130, 130, .9, 0), (140, 90, 160, 130, .9, 0),
                 (101, 90, 103, 130, .9, 2), (105, 90, 110, 130, .1, 0)]
        self.assertEqual(select_target(boxes, (100, 100), 100).x, 120)

    def test_outside_radius_and_local_character_excluded(self):
        boxes = [(0, 0, 200, 200, .9, 0), (300, 100, 350, 200, .9, 0)]
        self.assertIsNone(select_target(boxes, (100, 100), 50))

    def test_person_already_under_crosshair_remains_selected(self):
        target = select_target([(90, 85, 110, 135, .9, 0)], (100, 100), 25)
        self.assertIsNotNone(target)
        self.assertEqual(target.distance, 0)

    def test_proximity_does_not_select_distant_person(self):
        self.assertIsNone(select_target([(140, 85, 160, 135, .9, 0)], (100, 100), 25))


if __name__ == '__main__':
    unittest.main()
