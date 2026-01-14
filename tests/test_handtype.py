"""Tests for HandType comparison operators."""

import unittest

from maverick.enums import HandType


class TestHandTypeComparisons(unittest.TestCase):
    """Test HandType enum comparison operators."""

    def test_handtype_less_than(self):
        """Test __lt__ operator for HandType."""
        self.assertTrue(HandType.HIGH_CARD < HandType.PAIR)
        self.assertTrue(HandType.PAIR < HandType.TWO_PAIR)
        self.assertTrue(HandType.TWO_PAIR < HandType.THREE_OF_A_KIND)
        self.assertTrue(HandType.THREE_OF_A_KIND < HandType.STRAIGHT)
        self.assertTrue(HandType.STRAIGHT < HandType.FLUSH)
        self.assertTrue(HandType.FLUSH < HandType.FULL_HOUSE)
        self.assertTrue(HandType.FULL_HOUSE < HandType.FOUR_OF_A_KIND)
        self.assertTrue(HandType.FOUR_OF_A_KIND < HandType.STRAIGHT_FLUSH)
        self.assertTrue(HandType.STRAIGHT_FLUSH < HandType.ROYAL_FLUSH)

    def test_handtype_less_than_false(self):
        """Test __lt__ returns False when left is greater or equal."""
        self.assertFalse(HandType.PAIR < HandType.HIGH_CARD)
        self.assertFalse(HandType.ROYAL_FLUSH < HandType.STRAIGHT_FLUSH)
        self.assertFalse(HandType.PAIR < HandType.PAIR)

    def test_handtype_less_than_or_equal(self):
        """Test __le__ operator for HandType."""
        self.assertTrue(HandType.HIGH_CARD <= HandType.PAIR)
        self.assertTrue(HandType.PAIR <= HandType.PAIR)
        self.assertTrue(HandType.STRAIGHT <= HandType.FLUSH)
        self.assertTrue(HandType.ROYAL_FLUSH <= HandType.ROYAL_FLUSH)

    def test_handtype_less_than_or_equal_false(self):
        """Test __le__ returns False when left is greater."""
        self.assertFalse(HandType.PAIR <= HandType.HIGH_CARD)
        self.assertFalse(HandType.ROYAL_FLUSH <= HandType.STRAIGHT_FLUSH)

    def test_handtype_greater_than(self):
        """Test __gt__ operator for HandType."""
        self.assertTrue(HandType.PAIR > HandType.HIGH_CARD)
        self.assertTrue(HandType.TWO_PAIR > HandType.PAIR)
        self.assertTrue(HandType.THREE_OF_A_KIND > HandType.TWO_PAIR)
        self.assertTrue(HandType.STRAIGHT > HandType.THREE_OF_A_KIND)
        self.assertTrue(HandType.FLUSH > HandType.STRAIGHT)
        self.assertTrue(HandType.FULL_HOUSE > HandType.FLUSH)
        self.assertTrue(HandType.FOUR_OF_A_KIND > HandType.FULL_HOUSE)
        self.assertTrue(HandType.STRAIGHT_FLUSH > HandType.FOUR_OF_A_KIND)
        self.assertTrue(HandType.ROYAL_FLUSH > HandType.STRAIGHT_FLUSH)

    def test_handtype_greater_than_false(self):
        """Test __gt__ returns False when left is less or equal."""
        self.assertFalse(HandType.HIGH_CARD > HandType.PAIR)
        self.assertFalse(HandType.STRAIGHT_FLUSH > HandType.ROYAL_FLUSH)
        self.assertFalse(HandType.PAIR > HandType.PAIR)

    def test_handtype_greater_than_or_equal(self):
        """Test __ge__ operator for HandType."""
        self.assertTrue(HandType.PAIR >= HandType.HIGH_CARD)
        self.assertTrue(HandType.PAIR >= HandType.PAIR)
        self.assertTrue(HandType.FLUSH >= HandType.STRAIGHT)
        self.assertTrue(HandType.ROYAL_FLUSH >= HandType.ROYAL_FLUSH)

    def test_handtype_greater_than_or_equal_false(self):
        """Test __ge__ returns False when left is less."""
        self.assertFalse(HandType.HIGH_CARD >= HandType.PAIR)
        self.assertFalse(HandType.STRAIGHT_FLUSH >= HandType.ROYAL_FLUSH)

    def test_handtype_comparison_with_different_type_returns_not_implemented(self):
        """Test comparison with non-HandType returns NotImplemented."""
        # These comparisons should return NotImplemented, which Python will handle
        # by trying the reverse comparison or raising TypeError
        self.assertEqual(HandType.PAIR.__lt__(5), NotImplemented)
        self.assertEqual(HandType.PAIR.__le__(5), NotImplemented)
        self.assertEqual(HandType.PAIR.__gt__(5), NotImplemented)
        self.assertEqual(HandType.PAIR.__ge__(5), NotImplemented)

    def test_handtype_comparison_chain(self):
        """Test chained comparisons work correctly."""
        self.assertTrue(
            HandType.HIGH_CARD
            < HandType.PAIR
            < HandType.TWO_PAIR
            < HandType.ROYAL_FLUSH
        )
        self.assertTrue(
            HandType.ROYAL_FLUSH > HandType.STRAIGHT_FLUSH > HandType.FOUR_OF_A_KIND
        )

    def test_handtype_equality_with_same_type(self):
        """Test equality comparison between same HandType values."""
        self.assertEqual(HandType.PAIR, HandType.PAIR)
        self.assertEqual(HandType.ROYAL_FLUSH, HandType.ROYAL_FLUSH)
        self.assertNotEqual(HandType.PAIR, HandType.TWO_PAIR)

    def test_handtype_sorting(self):
        """Test that HandTypes can be sorted correctly."""
        hands = [
            HandType.ROYAL_FLUSH,
            HandType.HIGH_CARD,
            HandType.FLUSH,
            HandType.PAIR,
            HandType.STRAIGHT,
        ]
        sorted_hands = sorted(hands)
        expected = [
            HandType.HIGH_CARD,
            HandType.PAIR,
            HandType.STRAIGHT,
            HandType.FLUSH,
            HandType.ROYAL_FLUSH,
        ]
        self.assertEqual(sorted_hands, expected)

    def test_handtype_min_max(self):
        """Test that min and max work with HandTypes."""
        hands = [
            HandType.PAIR,
            HandType.FLUSH,
            HandType.HIGH_CARD,
            HandType.ROYAL_FLUSH,
        ]
        self.assertEqual(min(hands), HandType.HIGH_CARD)
        self.assertEqual(max(hands), HandType.ROYAL_FLUSH)

    def test_handtype_all_values_ordered_correctly(self):
        """Test that all HandType values are ordered from weakest to strongest."""
        all_hands = [
            HandType.HIGH_CARD,
            HandType.PAIR,
            HandType.TWO_PAIR,
            HandType.THREE_OF_A_KIND,
            HandType.STRAIGHT,
            HandType.FLUSH,
            HandType.FULL_HOUSE,
            HandType.FOUR_OF_A_KIND,
            HandType.STRAIGHT_FLUSH,
            HandType.ROYAL_FLUSH,
        ]

        # Check that each hand is less than all hands after it
        for i in range(len(all_hands) - 1):
            self.assertTrue(all_hands[i] < all_hands[i + 1])
            self.assertTrue(all_hands[i + 1] > all_hands[i])
            self.assertTrue(all_hands[i] <= all_hands[i + 1])
            self.assertTrue(all_hands[i + 1] >= all_hands[i])


if __name__ == "__main__":
    unittest.main()
