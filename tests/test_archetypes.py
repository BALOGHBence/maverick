import unittest

from maverick import Game, PlayerState
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
)


class TestArchetypeInstantiation(unittest.TestCase):
    """Test that all archetype classes can be instantiated."""

    def test_instantiate_tight_aggressive(self) -> None:
        bot = TightAggressiveBot(uid="tag", name="TAG")
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "TAG")

    def test_instantiate_loose_aggressive(self) -> None:
        bot = LooseAggressiveBot(uid="lag", name="LAG")
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "LAG")

    def test_instantiate_tight_passive(self) -> None:
        bot = TightPassiveBot(uid="tp", name="Rock")
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Rock")

    def test_instantiate_loose_passive(self) -> None:
        bot = LoosePassiveBot(uid="lp", name="Station")
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Station")

    def test_instantiate_maniac(self) -> None:
        bot = ManiacBot(uid="man", name="Maniac")
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Maniac")

    def test_instantiate_tilted(self) -> None:
        bot = TiltedBot(uid="tilt", name="Tilted")
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Tilted")

    def test_instantiate_bully(self) -> None:
        bot = BullyBot(uid="bully", name="Bully")
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Bully")

    def test_instantiate_grinder(self) -> None:
        bot = GrinderBot(uid="grind", name="Grinder")
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Grinder")

    def test_instantiate_gto(self) -> None:
        bot = GTOBot(uid="gto", name="GTO")
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "GTO")

    def test_instantiate_shark(self) -> None:
        bot = SharkBot(uid="shark", name="Shark")
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Shark")

    def test_instantiate_fish(self) -> None:
        bot = FishBot(uid="fish", name="Fish")
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Fish")

    def test_instantiate_abc(self) -> None:
        bot = ABCBot(uid="abc", name="ABC")
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "ABC")

    def test_instantiate_hero_caller(self) -> None:
        bot = HeroCallerBot(uid="hero", name="Hero")
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Hero")

    def test_instantiate_scared_money(self) -> None:
        bot = ScaredMoneyBot(uid="scared", name="Scared")
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Scared")

    def test_instantiate_whale(self) -> None:
        bot = WhaleBot(uid="whale", name="Whale")
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Whale")


class TestArchetypeGameplay(unittest.TestCase):
    """Test that archetype bots can play complete games."""

    def test_tight_aggressive_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            TightAggressiveBot(uid="p1", name="TAG"),
            state=PlayerState(stack=100, seat=0),
        )
        game.add_player(
            FoldBot(uid="p2", name="Fold"),
            state=PlayerState(stack=100, seat=1),
        )
        game.add_player(
            FoldBot(uid="p3", name="Fold2"),
            state=PlayerState(stack=100, seat=2),
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_loose_aggressive_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            LooseAggressiveBot(uid="p1", name="LAG"),
            state=PlayerState(stack=100, seat=0),
        )
        game.add_player(
            FoldBot(uid="p2", name="Fold"),
            state=PlayerState(stack=100, seat=1),
        )
        game.add_player(
            FoldBot(uid="p3", name="Fold2"),
            state=PlayerState(stack=100, seat=2),
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_tight_passive_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            TightPassiveBot(uid="p1", name="Rock"),
            state=PlayerState(stack=100, seat=0),
        )
        game.add_player(
            FoldBot(uid="p2", name="Fold"),
            state=PlayerState(stack=100, seat=1),
        )
        game.add_player(
            FoldBot(uid="p3", name="Fold2"),
            state=PlayerState(stack=100, seat=2),
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_loose_passive_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            LoosePassiveBot(uid="p1", name="Station"),
            state=PlayerState(stack=100, seat=0),
        )
        game.add_player(
            FoldBot(uid="p2", name="Fold"),
            state=PlayerState(stack=100, seat=1),
        )
        game.add_player(
            FoldBot(uid="p3", name="Fold2"),
            state=PlayerState(stack=100, seat=2),
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_maniac_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            ManiacBot(uid="p1", name="Maniac"),
            state=PlayerState(stack=100, seat=0),
        )
        game.add_player(
            FoldBot(uid="p2", name="Fold"),
            state=PlayerState(stack=100, seat=1),
        )
        game.add_player(
            FoldBot(uid="p3", name="Fold2"),
            state=PlayerState(stack=100, seat=2),
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_tilted_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            TiltedBot(uid="p1", name="Tilted"),
            state=PlayerState(stack=100, seat=0),
        )
        game.add_player(
            FoldBot(uid="p2", name="Fold"),
            state=PlayerState(stack=100, seat=1),
        )
        game.add_player(
            FoldBot(uid="p3", name="Fold2"),
            state=PlayerState(stack=100, seat=2),
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_bully_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            BullyBot(uid="p1", name="Bully"),
            state=PlayerState(stack=100, seat=0),
        )
        game.add_player(
            FoldBot(uid="p2", name="Fold"),
            state=PlayerState(stack=100, seat=1),
        )
        game.add_player(
            FoldBot(uid="p3", name="Fold2"),
            state=PlayerState(stack=100, seat=2),
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_grinder_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            GrinderBot(uid="p1", name="Grinder"),
            state=PlayerState(stack=100, seat=0),
        )
        game.add_player(
            FoldBot(uid="p2", name="Fold"),
            state=PlayerState(stack=100, seat=1),
        )
        game.add_player(
            FoldBot(uid="p3", name="Fold2"),
            state=PlayerState(stack=100, seat=2),
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_gto_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            GTOBot(uid="p1", name="GTO"),
            state=PlayerState(stack=100, seat=0),
        )
        game.add_player(
            FoldBot(uid="p2", name="Fold"),
            state=PlayerState(stack=100, seat=1),
        )
        game.add_player(
            FoldBot(uid="p3", name="Fold2"),
            state=PlayerState(stack=100, seat=2),
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_shark_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            SharkBot(uid="p1", name="Shark"),
            state=PlayerState(stack=100, seat=0),
        )
        game.add_player(
            FoldBot(uid="p2", name="Fold"),
            state=PlayerState(stack=100, seat=1),
        )
        game.add_player(
            FoldBot(uid="p3", name="Fold2"),
            state=PlayerState(stack=100, seat=2),
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_fish_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            FishBot(uid="p1", name="Fish"),
            state=PlayerState(stack=100, seat=0),
        )
        game.add_player(
            FoldBot(uid="p2", name="Fold"),
            state=PlayerState(stack=100, seat=1),
        )
        game.add_player(
            FoldBot(uid="p3", name="Fold2"),
            state=PlayerState(stack=100, seat=2),
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_abc_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            ABCBot(uid="p1", name="ABC"),
            state=PlayerState(stack=100, seat=0),
        )
        game.add_player(
            FoldBot(uid="p2", name="Fold"),
            state=PlayerState(stack=100, seat=1),
        )
        game.add_player(
            FoldBot(uid="p3", name="Fold2"),
            state=PlayerState(stack=100, seat=2),
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_hero_caller_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            HeroCallerBot(uid="p1", name="Hero"),
            state=PlayerState(stack=100, seat=0),
        )
        game.add_player(
            FoldBot(uid="p2", name="Fold"),
            state=PlayerState(stack=100, seat=1),
        )
        game.add_player(
            FoldBot(uid="p3", name="Fold2"),
            state=PlayerState(stack=100, seat=2),
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_scared_money_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            ScaredMoneyBot(uid="p1", name="Scared"),
            state=PlayerState(stack=100, seat=0),
        )
        game.add_player(
            FoldBot(uid="p2", name="Fold"),
            state=PlayerState(stack=100, seat=1),
        )
        game.add_player(
            FoldBot(uid="p3", name="Fold2"),
            state=PlayerState(stack=100, seat=2),
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_whale_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            WhaleBot(uid="p1", name="Whale"),
            state=PlayerState(stack=100, seat=0),
        )
        game.add_player(
            FoldBot(uid="p2", name="Fold"),
            state=PlayerState(stack=100, seat=1),
        )
        game.add_player(
            FoldBot(uid="p3", name="Fold2"),
            state=PlayerState(stack=100, seat=2),
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_mixed_archetypes_game(self) -> None:
        """Test a game with multiple different archetypes."""
        game = Game(small_blind=1, big_blind=2, max_hands=2)
        game.add_player(
            TightAggressiveBot(uid="p1", name="TAG"),
            state=PlayerState(stack=100, seat=0),
        )
        game.add_player(
            LoosePassiveBot(uid="p2", name="LP"),
            state=PlayerState(stack=100, seat=1),
        )
        game.add_player(
            ManiacBot(uid="p3", name="Maniac"),
            state=PlayerState(stack=100, seat=2),
        )
        game.start()
        self.assertGreaterEqual(game.state.hand_number, 1)


if __name__ == "__main__":
    unittest.main()
