import unittest


class TestSmokeImports(unittest.TestCase):
    def test_import_package(self) -> None:
        import maverick  # noqa: F401

    def test_import_core_symbols(self) -> None:
        from maverick import Deck, Holding, Hand, Game  # noqa: F401


class TestSmokeModels(unittest.TestCase):
    def test_deck_deal_unique_cards(self) -> None:
        from maverick import Deck

        deck = Deck.standard_deck(shuffle=True)
        cards = deck.deal(5)
        self.assertEqual(len(cards), 5)
        self.assertEqual(len({(c.suit, c.rank) for c in cards}), 5)

    def test_hand_score_returns_tuple(self) -> None:
        from maverick import Deck, Hand

        deck = Deck.standard_deck(shuffle=True)
        private = deck.deal(2)
        community = deck.deal(3)
        hand = Hand(private_cards=private, community_cards=community)

        hand_type, score = hand.score()
        self.assertIsNotNone(hand_type)
        self.assertIsInstance(score, float)


class TestSmokeGame(unittest.TestCase):
    def test_game_runs_single_hand(self) -> None:
        from maverick import Game
        from maverick.players import FoldBot

        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(FoldBot(id="p1", name="P1", stack=50, seat=0))
        game.add_player(FoldBot(id="p2", name="P2", stack=50, seat=1))

        # Should complete without raising
        game.start()

        # Game should have played exactly one hand
        self.assertEqual(game.state.hand_number, 1)


if __name__ == "__main__":
    unittest.main()
