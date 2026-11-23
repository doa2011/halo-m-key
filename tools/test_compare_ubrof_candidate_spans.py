"""独立快速反证：不使用专有 SDK，不构建 SDCC。"""
import unittest
from compare_ubrof_candidate_spans import compare_candidate_spans as compare


class TestCandidateSpanComparison(unittest.TestCase):
    def test_first_real_difference(self):
        r = compare(b"abX", 0, 3, b"abY", 0, 3, 3)
        self.assertEqual(r["first_difference_offset"], 2)
        self.assertTrue(r["divergence_observed"])
        self.assertFalse(r["hit_comparison_cap"])

    def test_cap_hides_later_difference(self):
        r = compare(b"abX", 0, 3, b"abY", 0, 3, 2)
        self.assertIsNone(r["first_difference_offset"])
        self.assertTrue(r["hit_comparison_cap"])
        self.assertTrue(r["equality_beyond_window_unknown"])

    def test_left_shorter(self):
        r = compare(b"abc", 0, 2, b"abc", 0, 3, 10)
        self.assertTrue(r["left_span_ended"])
        self.assertFalse(r["right_span_ended"])
        self.assertFalse(r["equality_beyond_window_unknown"])

    def test_right_shorter(self):
        r = compare(b"abc", 0, 3, b"abc", 0, 2, 10)
        self.assertTrue(r["right_span_ended"])
        self.assertFalse(r["left_span_ended"])

    def test_both_equal(self):
        r = compare(b"abc", 0, 3, b"abc", 0, 3, 10)
        self.assertTrue(r["hit_candidate_span_end"])
        self.assertFalse(r["divergence_observed"])
        self.assertFalse(r["candidate_boundaries_verified"])

    def test_empty_span(self):
        r = compare(b"a", 0, 0, b"a", 0, 1, 10)
        self.assertEqual(r["compared_bytes"], 0)
        self.assertTrue(r["left_span_ended"])

    def test_offset_alignment(self):
        r = compare(b"xxabcZ", 2, 6, b"yabcY", 1, 5, 10)
        self.assertEqual(r["first_difference_offset"], 3)

    def test_invalid_bounds_and_cap(self):
        for args in [
            (b"a", 0, 2, b"a", 0, 1, 10),
            (b"a", -1, 1, b"a", 0, 1, 10),
            (b"a", 0, 1, b"a", 0, 1, 0),
        ]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                compare(*args)


    def test_span_exactly_at_cap(self):
        # 两侧候选区间与 cap 同时结束：两个标记可以同时为真。
        r = compare(b"abcd", 0, 4, b"abcd", 0, 4, 4)
        self.assertEqual(r["common_bytes"], 4)
        self.assertTrue(r["hit_comparison_cap"])
        self.assertTrue(r["hit_candidate_span_end"])
        self.assertTrue(r["left_span_ended"])
        self.assertTrue(r["right_span_ended"])
        self.assertFalse(r["equality_beyond_window_unknown"])
        self.assertFalse(r["candidate_boundaries_verified"])

    def test_span_shorter_than_cap(self):
        # 候选区间提前结束不应报告比较上限截断。
        r = compare(b"abcde", 0, 3, b"abcde", 0, 5, 4)
        self.assertEqual(r["common_bytes"], 3)
        self.assertFalse(r["hit_comparison_cap"])
        self.assertTrue(r["hit_candidate_span_end"])
        self.assertTrue(r["left_span_ended"])
        self.assertFalse(r["right_span_ended"])
        self.assertFalse(r["equality_beyond_window_unknown"])

    def test_span_longer_than_cap(self):
        # 上限之外的真实差异必须保持未知，而非误报完全相等。
        r = compare(b"abcdX", 0, 5, b"abcdY", 0, 5, 4)
        self.assertEqual(r["common_bytes"], 4)
        self.assertTrue(r["hit_comparison_cap"])
        self.assertFalse(r["hit_candidate_span_end"])
        self.assertTrue(r["equality_beyond_window_unknown"])
        self.assertIsNone(r["first_difference_offset"])
        self.assertFalse(r["record_semantics_verified"])


if __name__ == "__main__":
    unittest.main()
