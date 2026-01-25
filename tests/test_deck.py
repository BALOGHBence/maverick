"""Tests for the Deck class."""

import unittest

from maverick import Deck


class TestDeckDealEdgeCases(unittest.TestCase):
    """Test edge cases for the Deck.deal() method."""

    def test_deck_deal_too_many_cards_raises_error(self):
        """Test that dealing more cards than available raises ValueError."""
        deck = Deck.build()
        with self.assertRaises(ValueError) as context:
            deck.deal(53)  # Trying to deal more than 52 cards
        self.assertIn("Not enough cards in the deck to deal", str(context.exception))

    def test_deck_deal_exactly_remaining_cards(self):
        """Test dealing exactly the remaining number of cards."""
        deck = Deck.build()
        deck.deal(50)  # Leave only 2 cards
        remaining = deck.deal(2)  # Deal the last 2 cards
        self.assertEqual(len(remaining), 2)
        self.assertEqual(len(deck.cards), 0)

    def test_deck_deal_from_empty_deck_raises_error(self):
        """Test that dealing from an empty deck raises ValueError."""
        deck = Deck.build()
        deck.deal(52)  # Deal all cards
        with self.assertRaises(ValueError) as context:
            deck.deal(1)
        self.assertIn("Not enough cards in the deck to deal", str(context.exception))

    def test_deck_deal_zero_cards_returns_empty_list(self):
        """Test that dealing 0 cards returns an empty list and issues a warning."""
        deck = Deck.build()
        initial_count = len(deck.cards)

        with self.assertWarns(UserWarning) as warning_context:
            result = deck.deal(0)

        self.assertEqual(result, [])
        self.assertEqual(len(deck.cards), initial_count)  # Deck unchanged
        self.assertIn("non-positive number of cards", str(warning_context.warning))

    def test_deck_deal_negative_cards_returns_empty_list(self):
        """Test that dealing negative number of cards returns empty list and issues a warning."""
        deck = Deck.build()
        initial_count = len(deck.cards)

        with self.assertWarns(UserWarning) as warning_context:
            result = deck.deal(-5)

        self.assertEqual(result, [])
        self.assertEqual(len(deck.cards), initial_count)  # Deck unchanged
        self.assertIn("non-positive number of cards", str(warning_context.warning))

    def test_deck_deal_one_card_from_full_deck(self):
        """Test dealing a single card from a full deck."""
        deck = Deck.build()
        result = deck.deal(1)
        self.assertEqual(len(result), 1)
        self.assertEqual(len(deck.cards), 51)

    def test_deck_deal_boundary_minus_one(self):
        """Test dealing exactly one less than the deck size."""
        deck = Deck.build()
        result = deck.deal(51)
        self.assertEqual(len(result), 51)
        self.assertEqual(len(deck.cards), 1)

    def test_deck_deal_all_cards(self):
        """Test dealing all 52 cards from a full deck."""
        deck = Deck.build()
        result = deck.deal(52)
        self.assertEqual(len(result), 52)
        self.assertEqual(len(deck.cards), 0)

    def test_deck_deal_after_partial_deal(self):
        """Test dealing more than remaining cards after a partial deal."""
        deck = Deck.build()
        deck.deal(30)  # 22 cards remaining
        with self.assertRaises(ValueError) as context:
            deck.deal(23)  # Try to deal more than remaining
        self.assertIn("Not enough cards in the deck to deal", str(context.exception))

    def test_shuffle_warns_on_negative_deal(self):
        """Test that shuffling the deck does not affect dealing negative cards."""
        deck = Deck.build()
        with self.assertWarns(UserWarning):
            deck.shuffle(n=-1)


if __name__ == "__main__":
    unittest.main()
