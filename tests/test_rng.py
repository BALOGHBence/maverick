"""Tests for the game's own random number generator (``Game(seed=...)``)."""

import random
import unittest

from maverick import Deck, Game, GameEventType, PlayerState
from maverick.players import CallBot


class RandomConsumingBot(CallBot):
    """Calls like CallBot, but uses up numbers from the global random module."""

    register = False  # don't replace CallBot in the cls_uid registry

    def decide_action(self, **kwargs):
        for _ in range(100):
            random.random()
        return super().decide_action(**kwargs)


def _cards(game: Game) -> list:
    """Plays the game and returns the cards of every hand."""
    hands = []

    def record(event, g: Game) -> None:
        hands.append(
            (
                [c.code() for c in g.state.community_cards],
                [
                    [c.code() for c in p.state.holding.cards]
                    for p in g.state.players
                    if p.state.holding is not None
                ],
            )
        )

    game.subscribe(GameEventType.SHOWDOWN_COMPLETED, record)
    game.start()
    return hands


def _game(*players, **kwargs) -> Game:
    kwargs.setdefault("max_hands", 5)
    game = Game(small_blind=1, big_blind=2, log_events=False, **kwargs)
    for player in players or (CallBot(name="a"), CallBot(name="b")):
        game.add_player(player, state=PlayerState(stack=1000))
    return game


class TestSeed(unittest.TestCase):
    def test_same_seed_deals_the_same_cards(self):
        first = _cards(_game(seed=42))
        self.assertEqual(len(first), 5)
        self.assertEqual(first, _cards(_game(seed=42)))

    def test_different_seeds_deal_different_cards(self):
        self.assertNotEqual(_cards(_game(seed=1)), _cards(_game(seed=2)))

    def test_seed_reproduces_a_game_without_explicit_seed(self):
        game = _game()
        self.assertIsInstance(game.seed, int)
        self.assertEqual(_cards(game), _cards(_game(seed=game.seed)))

    def test_seeding_global_random_still_works(self):
        random.seed(7)
        first = _cards(_game())
        random.seed(7)
        self.assertEqual(first, _cards(_game()))

    def test_players_using_random_dont_change_the_cards(self):
        plain = _cards(_game(seed=3))
        consuming = _cards(
            _game(RandomConsumingBot(name="a"), RandomConsumingBot(name="b"), seed=3)
        )
        self.assertEqual(plain, consuming)

    def test_first_button_draw_uses_the_seed(self):
        buttons = {
            _game(
                CallBot(name="a"), CallBot(name="b"), CallBot(name="c"), seed=s
            )._find_first_button_position()
            for s in (11, 11, 11)
        }
        self.assertEqual(len(buttons), 1)

    def test_seed_is_not_visible_to_players(self):
        game = _game(seed=123456789)
        self.assertNotIn("123456789", game.state.model_dump_json())
        self.assertNotIn(
            "123456789", str(game.get_player_view(game.state.players[0].uid))
        )

    def test_isolated_players_get_the_same_cards(self):
        in_process = _cards(_game(seed=5, player_isolation="none"))
        isolated = _cards(_game(seed=5, player_isolation="process"))
        self.assertEqual(in_process, isolated)

    def test_invalid_seed(self):
        for seed in ("42", 1.5, True):
            with self.subTest(seed=seed), self.assertRaises(ValueError):
                Game(small_blind=1, big_blind=2, seed=seed)


class TestDeckRng(unittest.TestCase):
    def test_shuffle_and_deal_with_rng(self):
        def draw(seed: int) -> list[str]:
            rng = random.Random(seed)
            deck = Deck.standard_deck(shuffle=True, rng=rng)
            return [c.code() for c in deck.deal(5, rng=rng)] + [
                c.code() for c in deck.cards
            ]

        self.assertEqual(draw(9), draw(9))
        self.assertNotEqual(draw(9), draw(10))

    def test_rng_is_independent_of_global_random(self):
        random.seed(1)
        first = Deck.build(shuffle=True, rng=random.Random(4)).cards
        random.seed(2)
        self.assertEqual(first, Deck.build(shuffle=True, rng=random.Random(4)).cards)


if __name__ == "__main__":
    unittest.main()
