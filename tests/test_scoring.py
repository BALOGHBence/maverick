import unittest

from maverick import Card, Suit, Rank, HandType, Deck, Hand
from maverick.utils.scoring import score_hand
import pandas as pd


class TestHandHierarchy(unittest.TestCase):
    """
    Test that hand scoring respects poker hand hierarchy across ALL possible hands.
    Ensures no overlap between hand type score ranges.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """Generate and score all possible 5-card poker hands once for all tests."""
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

    def test_high_card_vs_pair(self) -> None:
        """Test that the highest High Card score is less than the lowest Pair score."""
        df_high_cards = self.df[self.df["hand_type"] == "HIGH_CARD"]
        df_pairs = self.df[self.df["hand_type"] == "PAIR"]
        self.assertLess(df_high_cards["score"].max(), df_pairs["score"].min())

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


class TestScoringRankings(unittest.TestCase):
    """Test that hand rankings are correct."""

    def test_straight_beats_three_of_a_kind(self) -> None:
        """Verify straight (500+) scores higher than three of a kind (400+)."""
        # 5D 6S 3S 2S 4S = straight (2-3-4-5-6)
        straight = [
            Card(suit=Suit.DIAMONDS, rank=Rank.FIVE),
            Card(suit=Suit.SPADES, rank=Rank.SIX),
            Card(suit=Suit.SPADES, rank=Rank.THREE),
            Card(suit=Suit.SPADES, rank=Rank.TWO),
            Card(suit=Suit.SPADES, rank=Rank.FOUR),
        ]

        # 14C 12C 13C 14D 14S = three aces (A-A-A-K-Q)
        three_of_a_kind = [
            Card(suit=Suit.CLUBS, rank=Rank.ACE),
            Card(suit=Suit.CLUBS, rank=Rank.QUEEN),
            Card(suit=Suit.CLUBS, rank=Rank.KING),
            Card(suit=Suit.DIAMONDS, rank=Rank.ACE),
            Card(suit=Suit.SPADES, rank=Rank.ACE),
        ]

        straight_type, straight_score = score_hand(straight)
        three_type, three_score = score_hand(three_of_a_kind)

        self.assertEqual(straight_type, HandType.STRAIGHT)
        self.assertEqual(three_type, HandType.THREE_OF_A_KIND)
        self.assertGreater(
            straight_score,
            three_score,
            f"Straight ({straight_score}) should beat three of a kind ({three_score})",
        )

    def test_flush_beats_straight(self) -> None:
        """Verify flush (600+) scores higher than straight (500+)."""
        # All hearts: 2H 4H 6H 8H 10H (flush, no straight)
        flush = [
            Card(suit=Suit.HEARTS, rank=Rank.TWO),
            Card(suit=Suit.HEARTS, rank=Rank.FOUR),
            Card(suit=Suit.HEARTS, rank=Rank.SIX),
            Card(suit=Suit.HEARTS, rank=Rank.EIGHT),
            Card(suit=Suit.HEARTS, rank=Rank.TEN),
        ]

        # 2-3-4-5-6 mixed suits (straight, no flush)
        straight = [
            Card(suit=Suit.DIAMONDS, rank=Rank.TWO),
            Card(suit=Suit.SPADES, rank=Rank.THREE),
            Card(suit=Suit.CLUBS, rank=Rank.FOUR),
            Card(suit=Suit.HEARTS, rank=Rank.FIVE),
            Card(suit=Suit.DIAMONDS, rank=Rank.SIX),
        ]

        flush_type, flush_score = score_hand(flush)
        straight_type, straight_score = score_hand(straight)

        self.assertEqual(flush_type, HandType.FLUSH)
        self.assertEqual(straight_type, HandType.STRAIGHT)
        self.assertGreater(
            flush_score,
            straight_score,
            f"Flush ({flush_score}) should beat straight ({straight_score})",
        )

    def test_full_house_beats_flush(self) -> None:
        """Verify full house (700+) scores higher than flush (600+)."""
        # K-K-K-2-2 (full house)
        full_house = [
            Card(suit=Suit.HEARTS, rank=Rank.KING),
            Card(suit=Suit.DIAMONDS, rank=Rank.KING),
            Card(suit=Suit.CLUBS, rank=Rank.KING),
            Card(suit=Suit.SPADES, rank=Rank.TWO),
            Card(suit=Suit.HEARTS, rank=Rank.TWO),
        ]

        # All spades: AS KS QS JS 9S (flush)
        flush = [
            Card(suit=Suit.SPADES, rank=Rank.ACE),
            Card(suit=Suit.SPADES, rank=Rank.KING),
            Card(suit=Suit.SPADES, rank=Rank.QUEEN),
            Card(suit=Suit.SPADES, rank=Rank.JACK),
            Card(suit=Suit.SPADES, rank=Rank.NINE),
        ]

        fh_type, fh_score = score_hand(full_house)
        flush_type, flush_score = score_hand(flush)

        self.assertEqual(fh_type, HandType.FULL_HOUSE)
        self.assertEqual(flush_type, HandType.FLUSH)
        self.assertGreater(
            fh_score, flush_score, f"Full house ({fh_score}) should beat flush ({flush_score})"
        )


class TestArbitraryCardCounts(unittest.TestCase):
    """Test scoring with different numbers of cards."""

    def test_single_card(self) -> None:
        """Test with 1 card."""
        hand = [Card(suit=Suit.HEARTS, rank=Rank.ACE)]
        hand_type, score = score_hand(hand)
        self.assertEqual(hand_type, HandType.HIGH_CARD)
        self.assertGreater(score, 100)

    def test_three_cards(self) -> None:
        """Test with 3 cards."""
        hand = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.DIAMONDS, rank=Rank.ACE),
            Card(suit=Suit.CLUBS, rank=Rank.KING),
        ]
        hand_type, score = score_hand(hand)
        self.assertEqual(hand_type, HandType.PAIR)
        self.assertGreater(score, 200)

    def test_seven_cards(self) -> None:
        """Test with 7 cards (like Texas Hold'em)."""
        # 7-card hand with a flush
        hand = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.HEARTS, rank=Rank.KING),
            Card(suit=Suit.HEARTS, rank=Rank.QUEEN),
            Card(suit=Suit.HEARTS, rank=Rank.JACK),
            Card(suit=Suit.HEARTS, rank=Rank.TEN),
            Card(suit=Suit.SPADES, rank=Rank.TWO),
            Card(suit=Suit.CLUBS, rank=Rank.THREE),
        ]
        hand_type, score = score_hand(hand)
        # Should detect royal flush
        self.assertEqual(hand_type, HandType.ROYAL_FLUSH)
        self.assertEqual(score, 1000.0)


class TestStraightEdgeCases(unittest.TestCase):
    """Test special straight cases."""

    def test_wheel_straight(self) -> None:
        """Test A-2-3-4-5 (wheel) is recognized as straight."""
        hand = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.DIAMONDS, rank=Rank.TWO),
            Card(suit=Suit.CLUBS, rank=Rank.THREE),
            Card(suit=Suit.SPADES, rank=Rank.FOUR),
            Card(suit=Suit.HEARTS, rank=Rank.FIVE),
        ]
        hand_type, score = score_hand(hand)
        self.assertEqual(hand_type, HandType.STRAIGHT)
        self.assertGreater(score, 500)

    def test_broadway_straight(self) -> None:
        """Test 10-J-Q-K-A (broadway) is recognized as straight."""
        hand = [
            Card(suit=Suit.HEARTS, rank=Rank.TEN),
            Card(suit=Suit.DIAMONDS, rank=Rank.JACK),
            Card(suit=Suit.CLUBS, rank=Rank.QUEEN),
            Card(suit=Suit.SPADES, rank=Rank.KING),
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
        ]
        hand_type, score = score_hand(hand)
        self.assertEqual(hand_type, HandType.STRAIGHT)
        self.assertGreater(score, 500)

    def test_broadway_beats_wheel(self) -> None:
        """Test that 10-J-Q-K-A scores higher than A-2-3-4-5."""
        wheel = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.DIAMONDS, rank=Rank.TWO),
            Card(suit=Suit.CLUBS, rank=Rank.THREE),
            Card(suit=Suit.SPADES, rank=Rank.FOUR),
            Card(suit=Suit.HEARTS, rank=Rank.FIVE),
        ]
        broadway = [
            Card(suit=Suit.HEARTS, rank=Rank.TEN),
            Card(suit=Suit.DIAMONDS, rank=Rank.JACK),
            Card(suit=Suit.CLUBS, rank=Rank.QUEEN),
            Card(suit=Suit.SPADES, rank=Rank.KING),
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
        ]
        _, wheel_score = score_hand(wheel)
        _, broadway_score = score_hand(broadway)
        self.assertGreater(broadway_score, wheel_score)


class TestFlushVariations(unittest.TestCase):
    """Test flush detection with different scenarios."""

    def test_five_card_flush(self) -> None:
        """Test basic 5-card flush."""
        hand = [
            Card(suit=Suit.SPADES, rank=Rank.TWO),
            Card(suit=Suit.SPADES, rank=Rank.FIVE),
            Card(suit=Suit.SPADES, rank=Rank.SEVEN),
            Card(suit=Suit.SPADES, rank=Rank.NINE),
            Card(suit=Suit.SPADES, rank=Rank.KING),
        ]
        hand_type, score = score_hand(hand)
        self.assertEqual(hand_type, HandType.FLUSH)

    def test_six_card_flush(self) -> None:
        """Test 6-card flush (all same suit)."""
        hand = [
            Card(suit=Suit.DIAMONDS, rank=Rank.TWO),
            Card(suit=Suit.DIAMONDS, rank=Rank.FOUR),
            Card(suit=Suit.DIAMONDS, rank=Rank.SIX),
            Card(suit=Suit.DIAMONDS, rank=Rank.EIGHT),
            Card(suit=Suit.DIAMONDS, rank=Rank.TEN),
            Card(suit=Suit.DIAMONDS, rank=Rank.QUEEN),
        ]
        hand_type, score = score_hand(hand)
        self.assertEqual(hand_type, HandType.FLUSH)

    def test_ace_high_flush_beats_king_high(self) -> None:
        """Test that ace-high flush beats king-high flush."""
        ace_high = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.HEARTS, rank=Rank.NINE),
            Card(suit=Suit.HEARTS, rank=Rank.SEVEN),
            Card(suit=Suit.HEARTS, rank=Rank.FIVE),
            Card(suit=Suit.HEARTS, rank=Rank.THREE),
        ]
        king_high = [
            Card(suit=Suit.CLUBS, rank=Rank.KING),
            Card(suit=Suit.CLUBS, rank=Rank.QUEEN),
            Card(suit=Suit.CLUBS, rank=Rank.JACK),
            Card(suit=Suit.CLUBS, rank=Rank.TEN),
            Card(suit=Suit.CLUBS, rank=Rank.EIGHT),
        ]
        _, ace_score = score_hand(ace_high)
        _, king_score = score_hand(king_high)
        self.assertGreater(ace_score, king_score)


class TestPairComparisons(unittest.TestCase):
    """Test pair rankings and kicker logic."""

    def test_higher_pair_wins(self) -> None:
        """Test that pair of aces beats pair of twos."""
        aces = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.DIAMONDS, rank=Rank.ACE),
            Card(suit=Suit.CLUBS, rank=Rank.KING),
            Card(suit=Suit.SPADES, rank=Rank.QUEEN),
            Card(suit=Suit.HEARTS, rank=Rank.JACK),
        ]
        twos = [
            Card(suit=Suit.HEARTS, rank=Rank.TWO),
            Card(suit=Suit.DIAMONDS, rank=Rank.TWO),
            Card(suit=Suit.CLUBS, rank=Rank.ACE),
            Card(suit=Suit.SPADES, rank=Rank.KING),
            Card(suit=Suit.HEARTS, rank=Rank.QUEEN),
        ]
        _, ace_score = score_hand(aces)
        _, two_score = score_hand(twos)
        self.assertGreater(ace_score, two_score)

    def test_same_pair_higher_kicker_wins(self) -> None:
        """Test that same pair with higher kicker wins."""
        kings_ace_kicker = [
            Card(suit=Suit.HEARTS, rank=Rank.KING),
            Card(suit=Suit.DIAMONDS, rank=Rank.KING),
            Card(suit=Suit.CLUBS, rank=Rank.ACE),
            Card(suit=Suit.SPADES, rank=Rank.THREE),
            Card(suit=Suit.HEARTS, rank=Rank.TWO),
        ]
        kings_queen_kicker = [
            Card(suit=Suit.CLUBS, rank=Rank.KING),
            Card(suit=Suit.SPADES, rank=Rank.KING),
            Card(suit=Suit.DIAMONDS, rank=Rank.QUEEN),
            Card(suit=Suit.HEARTS, rank=Rank.JACK),
            Card(suit=Suit.CLUBS, rank=Rank.TEN),
        ]
        _, ace_kicker_score = score_hand(kings_ace_kicker)
        _, queen_kicker_score = score_hand(kings_queen_kicker)
        self.assertGreater(ace_kicker_score, queen_kicker_score)


class TestTwoPairComparisons(unittest.TestCase):
    """Test two pair rankings."""

    def test_higher_top_pair_wins(self) -> None:
        """Test that aces and twos beats kings and queens."""
        aces_twos = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.DIAMONDS, rank=Rank.ACE),
            Card(suit=Suit.CLUBS, rank=Rank.TWO),
            Card(suit=Suit.SPADES, rank=Rank.TWO),
            Card(suit=Suit.HEARTS, rank=Rank.THREE),
        ]
        kings_queens = [
            Card(suit=Suit.HEARTS, rank=Rank.KING),
            Card(suit=Suit.DIAMONDS, rank=Rank.KING),
            Card(suit=Suit.CLUBS, rank=Rank.QUEEN),
            Card(suit=Suit.SPADES, rank=Rank.QUEEN),
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
        ]
        _, aces_score = score_hand(aces_twos)
        _, kings_score = score_hand(kings_queens)
        self.assertGreater(aces_score, kings_score)

    def test_same_top_pair_higher_second_pair_wins(self) -> None:
        """Test that aces and kings beats aces and queens."""
        aces_kings = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.DIAMONDS, rank=Rank.ACE),
            Card(suit=Suit.CLUBS, rank=Rank.KING),
            Card(suit=Suit.SPADES, rank=Rank.KING),
            Card(suit=Suit.HEARTS, rank=Rank.TWO),
        ]
        aces_queens = [
            Card(suit=Suit.CLUBS, rank=Rank.ACE),
            Card(suit=Suit.SPADES, rank=Rank.ACE),
            Card(suit=Suit.DIAMONDS, rank=Rank.QUEEN),
            Card(suit=Suit.HEARTS, rank=Rank.QUEEN),
            Card(suit=Suit.CLUBS, rank=Rank.KING),
        ]
        _, kings_score = score_hand(aces_kings)
        _, queens_score = score_hand(aces_queens)
        self.assertGreater(kings_score, queens_score)


class TestThreeOfAKindComparisons(unittest.TestCase):
    """Test three of a kind rankings."""

    def test_higher_triple_wins(self) -> None:
        """Test that three aces beats three kings."""
        three_aces = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.DIAMONDS, rank=Rank.ACE),
            Card(suit=Suit.CLUBS, rank=Rank.ACE),
            Card(suit=Suit.SPADES, rank=Rank.TWO),
            Card(suit=Suit.HEARTS, rank=Rank.THREE),
        ]
        three_kings = [
            Card(suit=Suit.HEARTS, rank=Rank.KING),
            Card(suit=Suit.DIAMONDS, rank=Rank.KING),
            Card(suit=Suit.CLUBS, rank=Rank.KING),
            Card(suit=Suit.SPADES, rank=Rank.ACE),
            Card(suit=Suit.HEARTS, rank=Rank.QUEEN),
        ]
        _, aces_score = score_hand(three_aces)
        _, kings_score = score_hand(three_kings)
        self.assertGreater(aces_score, kings_score)


class TestFullHouseComparisons(unittest.TestCase):
    """Test full house rankings."""

    def test_higher_triple_wins_in_full_house(self) -> None:
        """Test that aces full of twos beats kings full of aces."""
        aces_full = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.DIAMONDS, rank=Rank.ACE),
            Card(suit=Suit.CLUBS, rank=Rank.ACE),
            Card(suit=Suit.SPADES, rank=Rank.TWO),
            Card(suit=Suit.HEARTS, rank=Rank.TWO),
        ]
        kings_full = [
            Card(suit=Suit.HEARTS, rank=Rank.KING),
            Card(suit=Suit.DIAMONDS, rank=Rank.KING),
            Card(suit=Suit.CLUBS, rank=Rank.KING),
            Card(suit=Suit.SPADES, rank=Rank.ACE),
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
        ]
        _, aces_score = score_hand(aces_full)
        _, kings_score = score_hand(kings_full)
        self.assertGreater(aces_score, kings_score)


class TestFourOfAKindComparisons(unittest.TestCase):
    """Test four of a kind rankings."""

    def test_higher_quad_wins(self) -> None:
        """Test that four aces beats four kings."""
        four_aces = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.DIAMONDS, rank=Rank.ACE),
            Card(suit=Suit.CLUBS, rank=Rank.ACE),
            Card(suit=Suit.SPADES, rank=Rank.ACE),
            Card(suit=Suit.HEARTS, rank=Rank.TWO),
        ]
        four_kings = [
            Card(suit=Suit.HEARTS, rank=Rank.KING),
            Card(suit=Suit.DIAMONDS, rank=Rank.KING),
            Card(suit=Suit.CLUBS, rank=Rank.KING),
            Card(suit=Suit.SPADES, rank=Rank.KING),
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
        ]
        _, aces_score = score_hand(four_aces)
        _, kings_score = score_hand(four_kings)
        self.assertGreater(aces_score, kings_score)


class TestStraightFlushAndRoyalFlush(unittest.TestCase):
    """Test straight flush and royal flush detection."""

    def test_straight_flush_detection(self) -> None:
        """Test that 5-6-7-8-9 all hearts is a straight flush."""
        hand = [
            Card(suit=Suit.HEARTS, rank=Rank.FIVE),
            Card(suit=Suit.HEARTS, rank=Rank.SIX),
            Card(suit=Suit.HEARTS, rank=Rank.SEVEN),
            Card(suit=Suit.HEARTS, rank=Rank.EIGHT),
            Card(suit=Suit.HEARTS, rank=Rank.NINE),
        ]
        hand_type, score = score_hand(hand)
        self.assertEqual(hand_type, HandType.STRAIGHT_FLUSH)
        self.assertGreater(score, 900)

    def test_royal_flush_beats_straight_flush(self) -> None:
        """Test that royal flush beats any other straight flush."""
        royal = [
            Card(suit=Suit.SPADES, rank=Rank.ACE),
            Card(suit=Suit.SPADES, rank=Rank.KING),
            Card(suit=Suit.SPADES, rank=Rank.QUEEN),
            Card(suit=Suit.SPADES, rank=Rank.JACK),
            Card(suit=Suit.SPADES, rank=Rank.TEN),
        ]
        straight_flush = [
            Card(suit=Suit.HEARTS, rank=Rank.NINE),
            Card(suit=Suit.HEARTS, rank=Rank.EIGHT),
            Card(suit=Suit.HEARTS, rank=Rank.SEVEN),
            Card(suit=Suit.HEARTS, rank=Rank.SIX),
            Card(suit=Suit.HEARTS, rank=Rank.FIVE),
        ]
        royal_type, royal_score = score_hand(royal)
        sf_type, sf_score = score_hand(straight_flush)
        
        self.assertEqual(royal_type, HandType.ROYAL_FLUSH)
        self.assertEqual(sf_type, HandType.STRAIGHT_FLUSH)
        self.assertGreater(royal_score, sf_score)


class TestHighCardComparisons(unittest.TestCase):
    """Test high card rankings."""

    def test_ace_high_beats_king_high(self) -> None:
        """Test that ace high beats king high when no pairs."""
        ace_high = [
            Card(suit=Suit.HEARTS, rank=Rank.ACE),
            Card(suit=Suit.DIAMONDS, rank=Rank.QUEEN),
            Card(suit=Suit.CLUBS, rank=Rank.TEN),
            Card(suit=Suit.SPADES, rank=Rank.EIGHT),
            Card(suit=Suit.HEARTS, rank=Rank.SIX),
        ]
        king_high = [
            Card(suit=Suit.HEARTS, rank=Rank.KING),
            Card(suit=Suit.DIAMONDS, rank=Rank.JACK),
            Card(suit=Suit.CLUBS, rank=Rank.NINE),
            Card(suit=Suit.SPADES, rank=Rank.SEVEN),
            Card(suit=Suit.HEARTS, rank=Rank.FIVE),
        ]
        _, ace_score = score_hand(ace_high)
        _, king_score = score_hand(king_high)
        self.assertGreater(ace_score, king_score)


if __name__ == "__main__":
    unittest.main()
