import unittest

from rdtx.window import SelectiveRepeatWindow


class SelectiveRepeatWindowTests(unittest.TestCase):
    def test_window_does_not_slide_past_missing_base_packet(self):
        window = SelectiveRepeatWindow(total_packets=10, window_size=4)

        self.assertEqual([window.take_next() for _ in range(4)], [0, 1, 2, 3])
        self.assertFalse(window.can_send)

        self.assertTrue(window.acknowledge(1))
        self.assertTrue(window.acknowledge(2))
        self.assertTrue(window.acknowledge(3))

        self.assertEqual(window.base, 0)
        self.assertFalse(window.can_send)

        self.assertTrue(window.acknowledge(0))
        self.assertEqual(window.base, 4)
        self.assertTrue(window.can_send)
        self.assertEqual(window.take_next(), 4)

    def test_base_advances_across_contiguous_acks(self):
        window = SelectiveRepeatWindow(total_packets=6, window_size=3)
        self.assertEqual([window.take_next() for _ in range(3)], [0, 1, 2])

        window.acknowledge(2)
        window.acknowledge(1)
        self.assertEqual(window.base, 0)

        window.acknowledge(0)
        self.assertEqual(window.base, 3)

    def test_duplicate_and_unsent_acks_are_ignored(self):
        window = SelectiveRepeatWindow(total_packets=3, window_size=2)
        window.take_next()

        self.assertFalse(window.acknowledge(2))
        self.assertTrue(window.acknowledge(0))
        self.assertFalse(window.acknowledge(0))
        self.assertEqual(window.acknowledged_count, 1)

    def test_empty_transfer_is_complete(self):
        window = SelectiveRepeatWindow(total_packets=0, window_size=8)
        self.assertTrue(window.complete)
        self.assertFalse(window.can_send)


if __name__ == "__main__":
    unittest.main()
