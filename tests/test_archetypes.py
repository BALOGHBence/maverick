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
)


class TestArchetypeInstantiation(unittest.TestCase):
    """Test that all archetype classes can be instantiated."""

    def test_instantiate_tight_aggressive(self) -> None:
        bot = TightAggressiveBot(
            id="tag", name="TAG", state=PlayerState(stack=100, seat=0)
        )
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "TAG")

    def test_instantiate_loose_aggressive(self) -> None:
        bot = LooseAggressiveBot(
            id="lag", name="LAG", state=PlayerState(stack=100, seat=0)
        )
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "LAG")

    def test_instantiate_tight_passive(self) -> None:
        bot = TightPassiveBot(
            id="tp", name="Rock", state=PlayerState(stack=100, seat=0)
        )
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Rock")

    def test_instantiate_loose_passive(self) -> None:
        bot = LoosePassiveBot(
            id="lp", name="Station", state=PlayerState(stack=100, seat=0)
        )
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Station")

    def test_instantiate_maniac(self) -> None:
        bot = ManiacBot(id="man", name="Maniac", state=PlayerState(stack=100, seat=0))
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Maniac")

    def test_instantiate_tilted(self) -> None:
        bot = TiltedBot(id="tilt", name="Tilted", state=PlayerState(stack=100, seat=0))
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Tilted")

    def test_instantiate_bully(self) -> None:
        bot = BullyBot(id="bully", name="Bully", state=PlayerState(stack=100, seat=0))
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Bully")

    def test_instantiate_grinder(self) -> None:
        bot = GrinderBot(
            id="grind", name="Grinder", state=PlayerState(stack=100, seat=0)
        )
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Grinder")

    def test_instantiate_gto(self) -> None:
        bot = GTOBot(id="gto", name="GTO", state=PlayerState(stack=100, seat=0))
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "GTO")

    def test_instantiate_shark(self) -> None:
        bot = SharkBot(id="shark", name="Shark", state=PlayerState(stack=100, seat=0))
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Shark")

    def test_instantiate_fish(self) -> None:
        bot = FishBot(id="fish", name="Fish", state=PlayerState(stack=100, seat=0))
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Fish")

    def test_instantiate_abc(self) -> None:
        bot = ABCBot(id="abc", name="ABC", state=PlayerState(stack=100, seat=0))
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "ABC")

    def test_instantiate_hero_caller(self) -> None:
        bot = HeroCallerBot(
            id="hero", name="Hero", state=PlayerState(stack=100, seat=0)
        )
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Hero")

    def test_instantiate_scared_money(self) -> None:
        bot = ScaredMoneyBot(
            id="scared", name="Scared", state=PlayerState(stack=100, seat=0)
        )
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Scared")

    def test_instantiate_whale(self) -> None:
        bot = WhaleBot(id="whale", name="Whale", state=PlayerState(stack=100, seat=0))
        self.assertIsNotNone(bot)
        self.assertEqual(bot.name, "Whale")


class TestArchetypeGameplay(unittest.TestCase):
    """Test that archetype bots can play complete games."""

    def test_tight_aggressive_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            TightAggressiveBot(
                id="p1", name="TAG", state=PlayerState(stack=100, seat=0)
            )
        )
        game.add_player(
            FoldBot(id="p2", name="Fold", state=PlayerState(stack=100, seat=1))
        )
        game.add_player(
            FoldBot(id="p3", name="Fold2", state=PlayerState(stack=100, seat=2))
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_loose_aggressive_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            LooseAggressiveBot(
                id="p1", name="LAG", state=PlayerState(stack=100, seat=0)
            )
        )
        game.add_player(
            FoldBot(id="p2", name="Fold", state=PlayerState(stack=100, seat=1))
        )
        game.add_player(
            FoldBot(id="p3", name="Fold2", state=PlayerState(stack=100, seat=2))
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_tight_passive_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            TightPassiveBot(id="p1", name="Rock", state=PlayerState(stack=100, seat=0))
        )
        game.add_player(
            FoldBot(id="p2", name="Fold", state=PlayerState(stack=100, seat=1))
        )
        game.add_player(
            FoldBot(id="p3", name="Fold2", state=PlayerState(stack=100, seat=2))
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_loose_passive_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            LoosePassiveBot(
                id="p1", name="Station", state=PlayerState(stack=100, seat=0)
            )
        )
        game.add_player(
            FoldBot(id="p2", name="Fold", state=PlayerState(stack=100, seat=1))
        )
        game.add_player(
            FoldBot(id="p3", name="Fold2", state=PlayerState(stack=100, seat=2))
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_maniac_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            ManiacBot(id="p1", name="Maniac", state=PlayerState(stack=100, seat=0))
        )
        game.add_player(
            FoldBot(id="p2", name="Fold", state=PlayerState(stack=100, seat=1))
        )
        game.add_player(
            FoldBot(id="p3", name="Fold2", state=PlayerState(stack=100, seat=2))
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_tilted_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            TiltedBot(id="p1", name="Tilted", state=PlayerState(stack=100, seat=0))
        )
        game.add_player(
            FoldBot(id="p2", name="Fold", state=PlayerState(stack=100, seat=1))
        )
        game.add_player(
            FoldBot(id="p3", name="Fold2", state=PlayerState(stack=100, seat=2))
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_bully_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            BullyBot(id="p1", name="Bully", state=PlayerState(stack=100, seat=0))
        )
        game.add_player(
            FoldBot(id="p2", name="Fold", state=PlayerState(stack=100, seat=1))
        )
        game.add_player(
            FoldBot(id="p3", name="Fold2", state=PlayerState(stack=100, seat=2))
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_grinder_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            GrinderBot(id="p1", name="Grinder", state=PlayerState(stack=100, seat=0))
        )
        game.add_player(
            FoldBot(id="p2", name="Fold", state=PlayerState(stack=100, seat=1))
        )
        game.add_player(
            FoldBot(id="p3", name="Fold2", state=PlayerState(stack=100, seat=2))
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_gto_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            GTOBot(id="p1", name="GTO", state=PlayerState(stack=100, seat=0))
        )
        game.add_player(
            FoldBot(id="p2", name="Fold", state=PlayerState(stack=100, seat=1))
        )
        game.add_player(
            FoldBot(id="p3", name="Fold2", state=PlayerState(stack=100, seat=2))
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_shark_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            SharkBot(id="p1", name="Shark", state=PlayerState(stack=100, seat=0))
        )
        game.add_player(
            FoldBot(id="p2", name="Fold", state=PlayerState(stack=100, seat=1))
        )
        game.add_player(
            FoldBot(id="p3", name="Fold2", state=PlayerState(stack=100, seat=2))
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_fish_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            FishBot(id="p1", name="Fish", state=PlayerState(stack=100, seat=0))
        )
        game.add_player(
            FoldBot(id="p2", name="Fold", state=PlayerState(stack=100, seat=1))
        )
        game.add_player(
            FoldBot(id="p3", name="Fold2", state=PlayerState(stack=100, seat=2))
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_abc_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            ABCBot(id="p1", name="ABC", state=PlayerState(stack=100, seat=0))
        )
        game.add_player(
            FoldBot(id="p2", name="Fold", state=PlayerState(stack=100, seat=1))
        )
        game.add_player(
            FoldBot(id="p3", name="Fold2", state=PlayerState(stack=100, seat=2))
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_hero_caller_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            HeroCallerBot(id="p1", name="Hero", state=PlayerState(stack=100, seat=0))
        )
        game.add_player(
            FoldBot(id="p2", name="Fold", state=PlayerState(stack=100, seat=1))
        )
        game.add_player(
            FoldBot(id="p3", name="Fold2", state=PlayerState(stack=100, seat=2))
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_scared_money_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            ScaredMoneyBot(id="p1", name="Scared", state=PlayerState(stack=100, seat=0))
        )
        game.add_player(
            FoldBot(id="p2", name="Fold", state=PlayerState(stack=100, seat=1))
        )
        game.add_player(
            FoldBot(id="p3", name="Fold2", state=PlayerState(stack=100, seat=2))
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_whale_game(self) -> None:
        game = Game(small_blind=1, big_blind=2, max_hands=1)
        game.add_player(
            WhaleBot(id="p1", name="Whale", state=PlayerState(stack=100, seat=0))
        )
        game.add_player(
            FoldBot(id="p2", name="Fold", state=PlayerState(stack=100, seat=1))
        )
        game.add_player(
            FoldBot(id="p3", name="Fold2", state=PlayerState(stack=100, seat=2))
        )
        game.start()
        self.assertEqual(game.state.hand_number, 1)

    def test_mixed_archetypes_game(self) -> None:
        """Test a game with multiple different archetypes."""
        game = Game(small_blind=1, big_blind=2, max_hands=2)
        game.add_player(
            TightAggressiveBot(
                id="p1", name="TAG", state=PlayerState(stack=100, seat=0)
            )
        )
        game.add_player(
            LoosePassiveBot(id="p2", name="LP", state=PlayerState(stack=100, seat=1))
        )
        game.add_player(
            ManiacBot(id="p3", name="Maniac", state=PlayerState(stack=100, seat=2))
        )
        game.start()
        self.assertGreaterEqual(game.state.hand_number, 1)


if __name__ == "__main__":
    unittest.main()
