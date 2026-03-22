"""Tests for the Deck class."""

import unittest
from collections import Counter

from maverick.players import FoldBot, CallBot, AggressiveBot
from maverick import (
    Game,
    PlayerState,
    PlayerStateType,
    GameState,
    GameStage,
    Street,
    Deck,
    GameEventType,
    PlayerSnapshot,
)


class TestGameFlowEdgeCases(unittest.TestCase):
    """Test edge cases related to the game flow."""

    def test_no_active_players_after_preflop(self):
        """Tests the scenario where all players go all-in pre-flop."""
        game = Game(small_blind=10, big_blind=20, max_hands=1)

        p1 = CallBot(name="CallBot")
        p2 = AggressiveBot(name="AggroBot")
        p3 = FoldBot(name="FoldBot")
        game.add_player(p1, state=PlayerState(stack=1000))
        game.add_player(p2, state=PlayerState(stack=1000))
        game.add_player(p3, state=PlayerState(stack=1000))

        snapshots = [
            PlayerSnapshot(uid=p1.uid, name=p1.name, state=PlayerState(
                seat=0, stack=0, state_type=PlayerStateType.ALL_IN,
                current_bet=1000, total_contributed=1000, acted_this_street=True,
            )),
            PlayerSnapshot(uid=p2.uid, name=p2.name, state=PlayerState(
                seat=1, stack=0, state_type=PlayerStateType.ALL_IN,
                current_bet=1000, total_contributed=1000, acted_this_street=True,
            )),
            PlayerSnapshot(uid=p3.uid, name=p3.name, state=PlayerState(
                seat=2, stack=0, state_type=PlayerStateType.ALL_IN,
                current_bet=1000, total_contributed=1000, acted_this_street=True,
            )),
        ]

        game._deck = Deck.standard_deck()
        game._state = GameState(
            stage=GameStage.PRE_FLOP,
            street=Street.PRE_FLOP,
            players=snapshots,
            current_player_index=2,
            community_cards=(),
            pot=3000,
            current_bet=1000,
            min_bet=1000,
            last_raise_size=1000,
            small_blind=10,
            big_blind=20,
            ante=0,
            hand_number=1,
            button_position=0,
        )

        game._event_queue.append(GameEventType.BETTING_ROUND_COMPLETED)
        self.assertTrue(game.has_events())
        self.assertEqual(game._event_queue[0], GameEventType.BETTING_ROUND_COMPLETED)

        _ = game.step()
        self.assertTrue(game.has_events())
        self.assertEqual(game._event_queue[0], GameEventType.FLOP_DEALT)

        _ = game.step()
        self.assertTrue(game.has_events())
        self.assertEqual(game._event_queue[0], GameEventType.BETTING_ROUND_COMPLETED)

    def test_players_eliminated_during_hand(self):
        """Tests the scenario where players are eliminated during a hand."""
        game = Game(small_blind=10, big_blind=20, max_hands=1)

        p1 = CallBot(name="CallBot")
        p2 = AggressiveBot(name="AggroBot")
        p3 = FoldBot(name="FoldBot")
        game.add_player(p1, state=PlayerState(stack=1000))
        game.add_player(p2, state=PlayerState(stack=1000))
        game.add_player(p3, state=PlayerState(stack=1000))

        snapshots = [
            PlayerSnapshot(uid=p1.uid, name=p1.name, state=PlayerState(
                seat=0, stack=0, state_type=PlayerStateType.ALL_IN,
                current_bet=1000, total_contributed=1000, acted_this_street=True,
            )),
            PlayerSnapshot(uid=p2.uid, name=p2.name, state=PlayerState(
                seat=1, stack=3000, state_type=PlayerStateType.ALL_IN,
                current_bet=1000, total_contributed=1000, acted_this_street=True,
            )),
            PlayerSnapshot(uid=p3.uid, name=p3.name, state=PlayerState(
                seat=2, stack=0, state_type=PlayerStateType.ALL_IN,
                current_bet=1000, total_contributed=1000, acted_this_street=True,
            )),
        ]

        game._deck = Deck.standard_deck()
        game._state = GameState(
            stage=GameStage.SHOWDOWN,
            street=None,
            players=snapshots,
            current_player_index=2,
            community_cards=(),
            pot=0,
            current_bet=0,
            min_bet=0,
            last_raise_size=0,
            small_blind=10,
            big_blind=20,
            ante=0,
            hand_number=1,
            button_position=0,
        )

        game._event_queue.append(GameEventType.SHOWDOWN_COMPLETED)
        self.assertTrue(game.has_events())
        self.assertEqual(game._event_queue[0], GameEventType.SHOWDOWN_COMPLETED)

        _ = game.step()
        self.assertTrue(game.has_events())
        self.assertEqual(game._event_queue[0], GameEventType.HAND_ENDED)

        _ = game.step()
        c = Counter(game._event_queue)
        self.assertEqual(c[GameEventType.PLAYER_ELIMINATED], 2)
        self.assertEqual(c[GameEventType.PLAYER_LEFT], 0)
        self.assertEqual(c[GameEventType.GAME_ENDED], 1)

    def test_eliminated_players_retained_in_state(self):
        """Eliminated players must remain in game.state.players with ELIMINATED state."""
        game = Game(small_blind=10, big_blind=20, max_hands=1)

        p1 = CallBot(name="CallBot")
        p2 = AggressiveBot(name="AggroBot")
        p3 = FoldBot(name="FoldBot")
        game.add_player(p1, state=PlayerState(stack=1000))
        game.add_player(p2, state=PlayerState(stack=1000))
        game.add_player(p3, state=PlayerState(stack=1000))

        # p2 wins everything; p1 and p3 are eliminated
        snapshots = [
            PlayerSnapshot(uid=p1.uid, name=p1.name, state=PlayerState(
                seat=0, stack=0, state_type=PlayerStateType.ALL_IN,
                current_bet=1000, total_contributed=1000, acted_this_street=True,
            )),
            PlayerSnapshot(uid=p2.uid, name=p2.name, state=PlayerState(
                seat=1, stack=3000, state_type=PlayerStateType.ALL_IN,
                current_bet=1000, total_contributed=1000, acted_this_street=True,
            )),
            PlayerSnapshot(uid=p3.uid, name=p3.name, state=PlayerState(
                seat=2, stack=0, state_type=PlayerStateType.ALL_IN,
                current_bet=1000, total_contributed=1000, acted_this_street=True,
            )),
        ]

        game._deck = Deck.standard_deck()
        game._state = GameState(
            stage=GameStage.SHOWDOWN,
            street=None,
            players=snapshots,
            current_player_index=2,
            community_cards=(),
            pot=0,
            current_bet=0,
            min_bet=0,
            last_raise_size=0,
            small_blind=10,
            big_blind=20,
            ante=0,
            hand_number=1,
            button_position=0,
        )

        game._event_queue.append(GameEventType.SHOWDOWN_COMPLETED)
        game._drain_event_queue()

        # All three players are still present in game.state.players
        self.assertEqual(len(game.state.players), 3)

        player_states = {s.uid: s for s in game.state.players}
        self.assertEqual(player_states[p1.uid].state.state_type, PlayerStateType.ELIMINATED)
        self.assertEqual(player_states[p2.uid].state.stack, 3000)
        self.assertEqual(player_states[p3.uid].state.state_type, PlayerStateType.ELIMINATED)

        # Non-eliminated players (p2 only) are visible via get_non_eliminated_players
        non_elim = game.state.get_non_eliminated_players()
        self.assertEqual(len(non_elim), 1)
        self.assertEqual(non_elim[0].uid, p2.uid)


if __name__ == "__main__":
    unittest.main()
