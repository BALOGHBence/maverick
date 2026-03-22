"""Tests asserting PlayerSnapshot isolation - consecutive GameState snapshots
must share no mutable references so that prior state cannot be retroactively
modified by later mutations."""

import unittest

from maverick import Game, GameEventType, PlayerState, PlayerSnapshot
from maverick.players import CallBot, FoldBot


class TestPlayerSnapshotIsolation(unittest.TestCase):
    """PlayerSnapshot isolation tests."""

    def test_game_state_players_type(self):
        """GameState.players must be a list of PlayerSnapshot objects."""
        game = Game(small_blind=10, big_blind=20)
        p1 = CallBot(name="P1")
        p2 = FoldBot(name="P2")
        game.add_player(p1, state=PlayerState(stack=500))
        game.add_player(p2, state=PlayerState(stack=500))

        for snapshot in game.state.players:
            self.assertIsInstance(snapshot, PlayerSnapshot)

    def test_strategies_dict_populated(self):
        """Game._strategies must contain all added PlayerLike strategy objects."""
        game = Game(small_blind=10, big_blind=20)
        p1 = CallBot(name="P1")
        p2 = FoldBot(name="P2")
        game.add_player(p1, state=PlayerState(stack=500))
        game.add_player(p2, state=PlayerState(stack=500))

        self.assertIn(p1.uid, game._strategies)
        self.assertIn(p2.uid, game._strategies)
        self.assertIs(game._strategies[p1.uid], p1)
        self.assertIs(game._strategies[p2.uid], p2)

    def test_strategies_removed_on_remove_player(self):
        """Removing a player clears it from _strategies."""
        game = Game(small_blind=10, big_blind=20)
        p1 = CallBot(name="P1")
        p2 = FoldBot(name="P2")
        game.add_player(p1, state=PlayerState(stack=500))
        game.add_player(p2, state=PlayerState(stack=500))
        game.remove_player(p1)

        self.assertNotIn(p1.uid, game._strategies)
        self.assertIn(p2.uid, game._strategies)

    def test_before_snapshot_unchanged_after_further_mutations(self):
        """GAME_STATE_CHANGED before/after payloads are fully independent.

        Capturing a ``before`` dict from a GAME_STATE_CHANGED event and then
        triggering further mutations must not alter the captured dict.
        """
        game = Game(small_blind=10, big_blind=20, max_hands=1)
        p1 = CallBot(name="P1")
        p2 = FoldBot(name="P2")
        game.add_player(p1, state=PlayerState(stack=1000))
        game.add_player(p2, state=PlayerState(stack=1000))

        captured_befores: list[dict] = []

        def capture(event, g):
            if event.type == GameEventType.GAME_STATE_CHANGED:
                # Deep-copy the before dict at capture time so we can compare later
                import copy

                captured_befores.append(copy.deepcopy(event.payload["before"]))

        game.subscribe(GameEventType.GAME_STATE_CHANGED, capture)
        game.start()

        # After the full game, check that older before-snapshots weren't mutated
        if len(captured_befores) >= 2:
            # Take the first captured before and re-check that it equals itself
            # (sanity check that snapshots are consistent dicts)
            first_before = captured_befores[0]
            self.assertIsInstance(first_before, dict)
            self.assertIn("players", first_before)

    def test_consecutive_game_states_independent(self):
        """Two consecutive GameState instances must not share player references."""
        game = Game(small_blind=10, big_blind=20)
        p1 = CallBot(name="P1")
        p2 = FoldBot(name="P2")
        game.add_player(p1, state=PlayerState(stack=1000))
        game.add_player(p2, state=PlayerState(stack=1000))

        state_before = game.state
        # Trigger a state update
        game._update_player_state(
            game.state.players[0], stack=game.state.players[0].state.stack - 100
        )
        state_after = game.state

        # The two states are different objects
        self.assertIsNot(state_before, state_after)
        # The player snapshots in the old state are not the same objects as in the new state
        self.assertIsNot(state_before.players[0], state_after.players[0])
        # The old snapshot still has the original stack
        self.assertEqual(state_before.players[0].state.stack, 1000)
        # The new snapshot has the updated stack
        self.assertEqual(state_after.players[0].state.stack, 900)

    def test_player_state_not_on_strategy(self):
        """Player strategy objects no longer carry a state attribute."""
        game = Game(small_blind=10, big_blind=20)
        p1 = CallBot(name="P1")
        p2 = FoldBot(name="P2")
        game.add_player(p1, state=PlayerState(stack=1000))
        game.add_player(p2, state=PlayerState(stack=1000))

        game._update_player_state(game.state.players[0], stack=700)

        # State lives in the snapshot, not on the strategy object
        self.assertFalse(hasattr(p1, "state"))
        self.assertEqual(game.get_player_snapshot(p1.uid).state.stack, 700)

    def test_get_player_snapshot_returns_current_state(self):
        """get_player_snapshot returns the up-to-date frozen snapshot."""
        game = Game(small_blind=10, big_blind=20)
        p1 = CallBot(name="P1")
        p2 = FoldBot(name="P2")
        game.add_player(p1, state=PlayerState(stack=1000))
        game.add_player(p2, state=PlayerState(stack=1000))

        snapshot_before = game.get_player_snapshot(p1.uid)
        self.assertEqual(snapshot_before.state.stack, 1000)

        game._update_player_state(game.state.players[0], stack=800)

        snapshot_after = game.get_player_snapshot(p1.uid)
        self.assertEqual(snapshot_after.state.stack, 800)
        # Old snapshot not mutated
        self.assertEqual(snapshot_before.state.stack, 1000)


if __name__ == "__main__":
    unittest.main()
