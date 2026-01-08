import unittest
from maverick import Deck, Hand
from maverick.utils import score_hand
import pandas as pd


class TestHierarchicalScoring(unittest.TestCase):
    """
    Test that hand scoring respects poker hand hierarchy.
    For example, the highest scoring Pair should be less than the lowest scoring Two Pair.
    """

    @classmethod
    def setUpClass(cls) -> None:
        deck = Deck.standard_deck(shuffle=True)
        all_possible_hands = list(Hand.all_possible_hands(deck.cards))

        hands_data = []
        for hand in all_possible_hands:
            cards = hand.private_cards + hand.community_cards
            hand_type, score = score_hand(cards)
            hand_data = {
                "hand": " ".join([f"{c.rank.value}{c.suit.value}" for c in cards]),
                "score": score,
                "hand_type": hand_type.name,
            }
            hands_data.append(hand_data)

        cls.df = pd.DataFrame(hands_data)

    def test_pairs_vs_two_pairs(self) -> None:
        """Test that the highest Pair score is less than the lowest Two Pair score."""
        df_pairs = self.df[self.df["hand_type"] == "PAIR"]
        df_two_pairs = self.df[self.df["hand_type"] == "TWO_PAIR"]
        self.assertLess(df_pairs["score"].max(), df_two_pairs["score"].min())

    def test_two_pairs_vs_three_of_a_kind(self) -> None:
        """Test that the highest Two Pair score is less than the lowest Three of a Kind score."""
        df_two_pairs = self.df[self.df["hand_type"] == "TWO_PAIR"]
        df_drills = self.df[self.df["hand_type"] == "THREE_OF_A_KIND"]
        self.assertLess(df_two_pairs["score"].max(), df_drills["score"].min())

    def test_three_of_a_kind_vs_straight(self) -> None:
        """Test that the highest Three of a Kind score is less than the lowest Straight score."""
        df_drills = self.df[self.df["hand_type"] == "THREE_OF_A_KIND"]
        df_straights = self.df[self.df["hand_type"] == "STRAIGHT"]
        self.assertLess(df_drills["score"].max(), df_straights["score"].min())

    def test_straight_vs_flush(self) -> None:
        """Test that the highest Straight score is less than the lowest Flush score."""
        df_straights = self.df[self.df["hand_type"] == "STRAIGHT"]
        df_flushes = self.df[self.df["hand_type"] == "FLUSH"]
        self.assertLess(df_straights["score"].max(), df_flushes["score"].min())

    def test_flush_vs_full_house(self) -> None:
        """Test that the highest Flush score is less than the lowest Full House score."""
        df_flushes = self.df[self.df["hand_type"] == "FLUSH"]
        df_full_houses = self.df[self.df["hand_type"] == "FULL_HOUSE"]
        self.assertLess(df_flushes["score"].max(), df_full_houses["score"].min())

    def test_full_house_vs_four_of_a_kind(self) -> None:
        """Test that the highest Full House score is less than the lowest Four of a Kind score."""
        df_full_houses = self.df[self.df["hand_type"] == "FULL_HOUSE"]
        df_four_of_a_kinds = self.df[self.df["hand_type"] == "FOUR_OF_A_KIND"]
        self.assertLess(
            df_full_houses["score"].max(), df_four_of_a_kinds["score"].min()
        )

    def test_four_of_a_kind_vs_straight_flush(self) -> None:
        """Test that the highest Four of a Kind score is less than the lowest Straight Flush score."""
        df_four_of_a_kinds = self.df[self.df["hand_type"] == "FOUR_OF_A_KIND"]
        df_straight_flushes = self.df[self.df["hand_type"] == "STRAIGHT_FLUSH"]
        self.assertLess(
            df_four_of_a_kinds["score"].max(), df_straight_flushes["score"].min()
        )

    def test_straight_flush_vs_royal_flush(self) -> None:
        """Test that the highest Straight Flush score is less than the lowest Royal Flush score."""
        df_straight_flushes = self.df[self.df["hand_type"] == "STRAIGHT_FLUSH"]
        df_royal_flushes = self.df[self.df["hand_type"] == "ROYAL_FLUSH"]
        self.assertLess(
            df_straight_flushes["score"].max(), df_royal_flushes["score"].min()
        )
