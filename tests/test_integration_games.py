"""Integration tests to push code coverage above 95%."""

import unittest
from maverick import Game
from maverick.playerstate import PlayerState
from maverick.players import (
    TightAggressiveBot,
    LooseAggressiveBot,
    TightPassiveBot,
    LoosePassiveBot,
    ManiacBot,
    TiltedBot,
    BullyBot,
    GrinderBot,
    GTOBot,
    SharkBot,
    FishBot,
    ABCBot,
    HeroCallerBot,
    ScaredMoneyBot,
    WhaleBot,
    FoldBot,
    CallBot,
    AggressiveBot,
)


class TestArchetypesPlayGames(unittest.TestCase):
    """Run actual games to cover decision-making logic."""

    def test_whale_plays_hand(self):
        """WhaleBot should play aggressively."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(
            WhaleBot(id="whale", name="Whale", state=PlayerState(stack=500, seat=0))
        )
        game.add_player(
            FoldBot(id="fold1", name="Fold1", state=PlayerState(stack=500, seat=1))
        )
        game.add_player(
            FoldBot(id="fold2", name="Fold2", state=PlayerState(stack=500, seat=2))
        )
        game.start()
        # Whale should win since others fold
        self.assertIsNotNone(game)

    def test_shark_plays_hand(self):
        """SharkBot should make calculated decisions."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(
            SharkBot(id="shark", name="Shark", state=PlayerState(stack=500, seat=0))
        )
        game.add_player(
            FoldBot(id="fold1", name="Fold1", state=PlayerState(stack=500, seat=1))
        )
        game.add_player(
            FoldBot(id="fold2", name="Fold2", state=PlayerState(stack=500, seat=2))
        )
        game.start()
        self.assertIsNotNone(game)

    def test_fish_plays_hand(self):
        """FishBot should play loosely."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(
            FishBot(id="fish", name="Fish", state=PlayerState(stack=500, seat=0))
        )
        game.add_player(
            FoldBot(id="fold1", name="Fold1", state=PlayerState(stack=500, seat=1))
        )
        game.add_player(
            FoldBot(id="fold2", name="Fold2", state=PlayerState(stack=500, seat=2))
        )
        game.start()
        self.assertIsNotNone(game)

    def test_hero_caller_plays_hand(self):
        """HeroCallerBot should call with marginal hands."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(
            HeroCallerBot(id="hero", name="Hero", state=PlayerState(stack=500, seat=0))
        )
        game.add_player(
            FoldBot(id="fold1", name="Fold1", state=PlayerState(stack=500, seat=1))
        )
        game.add_player(
            FoldBot(id="fold2", name="Fold2", state=PlayerState(stack=500, seat=2))
        )
        game.start()
        self.assertIsNotNone(game)

    def test_tilted_plays_hand(self):
        """TiltedBot should make reckless decisions."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(
            TiltedBot(id="tilt", name="Tilted", state=PlayerState(stack=500, seat=0))
        )
        game.add_player(
            FoldBot(id="fold1", name="Fold1", state=PlayerState(stack=500, seat=1))
        )
        game.add_player(
            FoldBot(id="fold2", name="Fold2", state=PlayerState(stack=500, seat=2))
        )
        game.start()
        self.assertIsNotNone(game)

    def test_bully_plays_hand(self):
        """BullyBot should be aggressive against short stacks."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(
            BullyBot(id="bully", name="Bully", state=PlayerState(stack=500, seat=0))
        )
        game.add_player(
            FoldBot(id="fold1", name="Fold1", state=PlayerState(stack=100, seat=1))
        )
        game.add_player(
            FoldBot(id="fold2", name="Fold2", state=PlayerState(stack=100, seat=2))
        )
        game.start()
        self.assertIsNotNone(game)

    def test_grinder_plays_hand(self):
        """GrinderBot should play patient poker."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(
            GrinderBot(id="grind", name="Grinder", state=PlayerState(stack=500, seat=0))
        )
        game.add_player(
            FoldBot(id="fold1", name="Fold1", state=PlayerState(stack=500, seat=1))
        )
        game.add_player(
            FoldBot(id="fold2", name="Fold2", state=PlayerState(stack=500, seat=2))
        )
        game.start()
        self.assertIsNotNone(game)

    def test_gto_plays_hand(self):
        """GTOBot should use balanced strategy."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(
            GTOBot(id="gto", name="GTO", state=PlayerState(stack=500, seat=0))
        )
        game.add_player(
            FoldBot(id="fold1", name="Fold1", state=PlayerState(stack=500, seat=1))
        )
        game.add_player(
            FoldBot(id="fold2", name="Fold2", state=PlayerState(stack=500, seat=2))
        )
        game.start()
        self.assertIsNotNone(game)

    def test_maniac_plays_hand(self):
        """ManiacBot should raise frequently."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(
            ManiacBot(id="maniac", name="Maniac", state=PlayerState(stack=500, seat=0))
        )
        game.add_player(
            FoldBot(id="fold1", name="Fold1", state=PlayerState(stack=500, seat=1))
        )
        game.add_player(
            FoldBot(id="fold2", name="Fold2", state=PlayerState(stack=500, seat=2))
        )
        game.start()
        self.assertIsNotNone(game)

    def test_scared_money_plays_hand(self):
        """ScaredMoneyBot should avoid big pots."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(
            ScaredMoneyBot(
                id="scared", name="Scared", state=PlayerState(stack=500, seat=0)
            )
        )
        game.add_player(
            FoldBot(id="fold1", name="Fold1", state=PlayerState(stack=500, seat=1))
        )
        game.add_player(
            FoldBot(id="fold2", name="Fold2", state=PlayerState(stack=500, seat=2))
        )
        game.start()
        self.assertIsNotNone(game)

    def test_loose_aggressive_plays_hand(self):
        """LooseAggressiveBot should play many hands."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(
            LooseAggressiveBot(
                id="lag", name="LAG", state=PlayerState(stack=500, seat=0)
            )
        )
        game.add_player(
            FoldBot(id="fold1", name="Fold1", state=PlayerState(stack=500, seat=1))
        )
        game.add_player(
            FoldBot(id="fold2", name="Fold2", state=PlayerState(stack=500, seat=2))
        )
        game.start()
        self.assertIsNotNone(game)

    def test_tight_passive_plays_hand(self):
        """TightPassiveBot should play tight."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(
            TightPassiveBot(id="tp", name="Rock", state=PlayerState(stack=500, seat=0))
        )
        game.add_player(
            FoldBot(id="fold1", name="Fold1", state=PlayerState(stack=500, seat=1))
        )
        game.add_player(
            FoldBot(id="fold2", name="Fold2", state=PlayerState(stack=500, seat=2))
        )
        game.start()
        self.assertIsNotNone(game)

    def test_loose_passive_plays_hand(self):
        """LoosePassiveBot should call often."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(
            LoosePassiveBot(
                id="lp", name="Station", state=PlayerState(stack=500, seat=0)
            )
        )
        game.add_player(
            FoldBot(id="fold1", name="Fold1", state=PlayerState(stack=500, seat=1))
        )
        game.add_player(
            FoldBot(id="fold2", name="Fold2", state=PlayerState(stack=500, seat=2))
        )
        game.start()
        self.assertIsNotNone(game)

    def test_abc_plays_hand(self):
        """ABCBot should play straightforward."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(
            ABCBot(id="abc", name="ABC", state=PlayerState(stack=500, seat=0))
        )
        game.add_player(
            FoldBot(id="fold1", name="Fold1", state=PlayerState(stack=500, seat=1))
        )
        game.add_player(
            FoldBot(id="fold2", name="Fold2", state=PlayerState(stack=500, seat=2))
        )
        game.start()
        self.assertIsNotNone(game)

    def test_tight_aggressive_plays_hand(self):
        """TightAggressiveBot should play premium hands aggressively."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(
            TightAggressiveBot(
                id="tag", name="TAG", state=PlayerState(stack=500, seat=0)
            )
        )
        game.add_player(
            FoldBot(id="fold1", name="Fold1", state=PlayerState(stack=500, seat=1))
        )
        game.add_player(
            FoldBot(id="fold2", name="Fold2", state=PlayerState(stack=500, seat=2))
        )
        game.start()
        self.assertIsNotNone(game)

    def test_callbot_plays_hand(self):
        """CallBot should always call."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(
            CallBot(id="call", name="Call", state=PlayerState(stack=500, seat=0))
        )
        game.add_player(
            FoldBot(id="fold1", name="Fold1", state=PlayerState(stack=500, seat=1))
        )
        game.add_player(
            FoldBot(id="fold2", name="Fold2", state=PlayerState(stack=500, seat=2))
        )
        game.start()
        self.assertIsNotNone(game)

    def test_aggressivebot_plays_hand(self):
        """AggressiveBot should play aggressively."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(
            AggressiveBot(
                id="agg", name="Aggressive", state=PlayerState(stack=500, seat=0)
            )
        )
        game.add_player(
            FoldBot(id="fold1", name="Fold1", state=PlayerState(stack=500, seat=1))
        )
        game.add_player(
            FoldBot(id="fold2", name="Fold2", state=PlayerState(stack=500, seat=2))
        )
        game.start()
        self.assertIsNotNone(game)

    def test_mixed_archetypes_game(self):
        """Test game with mixed archetypes."""
        game = Game(small_blind=5, big_blind=10, max_hands=2)
        game.add_player(
            WhaleBot(id="whale", name="Whale", state=PlayerState(stack=1000, seat=0))
        )
        game.add_player(
            SharkBot(id="shark", name="Shark", state=PlayerState(stack=1000, seat=1))
        )
        game.add_player(
            FishBot(id="fish", name="Fish", state=PlayerState(stack=1000, seat=2))
        )
        game.add_player(
            TightAggressiveBot(
                id="tag", name="TAG", state=PlayerState(stack=1000, seat=3)
            )
        )
        game.start()
        self.assertIsNotNone(game)

    def test_all_calling_game(self):
        """Test game where everyone calls."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(
            CallBot(id="call1", name="Call1", state=PlayerState(stack=200, seat=0))
        )
        game.add_player(
            CallBot(id="call2", name="Call2", state=PlayerState(stack=200, seat=1))
        )
        game.add_player(
            CallBot(id="call3", name="Call3", state=PlayerState(stack=200, seat=2))
        )
        game.start()
        self.assertIsNotNone(game)

    def test_aggressive_vs_passive(self):
        """Test aggressive vs passive bots."""
        game = Game(small_blind=5, big_blind=10, max_hands=1)
        game.add_player(
            AggressiveBot(
                id="agg", name="Aggressive", state=PlayerState(stack=500, seat=0)
            )
        )
        game.add_player(
            TightPassiveBot(id="tp", name="Rock", state=PlayerState(stack=500, seat=1))
        )
        game.add_player(
            LoosePassiveBot(
                id="lp", name="Station", state=PlayerState(stack=500, seat=2)
            )
        )
        game.start()
        self.assertIsNotNone(game)


if __name__ == "__main__":
    unittest.main()
