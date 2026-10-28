import unittest
from softlock import SoftLock
from targeting import Target


class SoftLockTests(unittest.TestCase):
    def setUp(self):
        self.gate = SoftLock()
        self.target = Target(100, 100, 0)

    def acquire(self):
        self.assertIsNone(self.gate.update(self.target, 0))
        self.assertIsNone(self.gate.update(self.target, .20))
        self.assertEqual(self.gate.update(self.target, .25), self.target)

    def test_continuous_acquisition(self):
        self.acquire()

    def test_missing_detection_releases_and_restarts(self):
        self.acquire()
        self.assertIsNone(self.gate.update(None, .30))
        self.assertIsNone(self.gate.update(self.target, .35))

    def test_target_jump_requires_acquisition(self):
        self.acquire()
        self.assertIsNone(self.gate.update(Target(200, 100, 0), .30))

    def test_long_inference_gap_does_not_count_as_acquisition(self):
        self.gate.update(self.target, 0)
        self.assertIsNone(self.gate.update(self.target, 1))

    def test_hold_expires_after_two_and_half_seconds(self):
        self.acquire()
        for i in range(1, 10):
            self.assertEqual(self.gate.update(self.target, .25 + i * .25), self.target)
        self.assertIsNone(self.gate.update(self.target, 2.75))

    def test_focus_reset_releases(self):
        self.acquire()
        self.gate.reset()
        self.assertIsNone(self.gate.update(self.target, .3))
