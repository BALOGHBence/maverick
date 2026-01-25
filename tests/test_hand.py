"""Tests for the Hand class."""

import unittest

from maverick import Hand, Deck


class TestHandEdgeCases(unittest.TestCase):
    """Test edge cases for the Hand class."""

    def test_all_possible_hands(self):
        """Test all possible hands generation."""
        deck = Deck.standard_deck(shuffle=True)
        private_cards = deck.deal(2)
        community_cards = deck.deal(5)
        hands = Hand.all_possible_hands(
            private_cards=private_cards, community_cards=community_cards
        )
        hand = next(hands)
        self.assertIsInstance(hand, Hand)


if __name__ == "__main__":
    unittest.main()
