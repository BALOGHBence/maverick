"""Deterministic tests for branches that games with random cards only reach sometimes.

Without these, coverage changes from run to run, depending on the cards dealt.
"""

import unittest

from maverick import (
    ActionType,
    Card,
    Game,
    GameStage,
    Holding,
    PlayerAction,
    PlayerState,
    PlayerStateType,
    Rank,
    Suit,
)
from maverick.players import CallBot
from maverick.utils import estimate_holding_strength

# A royal flush on the board: every player still in the hand ties
ROYAL_FLUSH = [
    Card(suit=Suit.SPADES, rank=rank)
    for rank in (Rank.ACE, Rank.KING, Rank.QUEEN, Rank.JACK, Rank.TEN)
]


def _holding(*cards: tuple[Suit, Rank]) -> Holding:
    return Holding(cards=[Card(suit=suit, rank=rank) for suit, rank in cards])


def _game_after_blinds(stacks: dict[str, int]) -> tuple[Game, dict[str, CallBot]]:
    """A game with the blinds posted: p1 is the button and acts first, p2 posts the
    small blind (10) and p3 the big blind (20)."""
    game = Game(
        small_blind=10,
        big_blind=20,
        max_hands=1,
        first_button_position=0,
        log_events=False,
    )
    players = {uid: CallBot(uid=uid, name=uid) for uid in stacks}
    for uid, stack in stacks.items():
        game.add_player(players[uid], state=PlayerState(stack=stack))
    game._initialize_game()
    game._start_new_hand()
    game._deal_hole_cards()
    game._post_blinds()
    return game, players


class TestRegisterPlayerAction(unittest.TestCase):
    def test_all_in_below_the_current_bet_doesnt_change_it(self):
        game, players = _game_after_blinds({"p1": 15, "p2": 1000, "p3": 1000})
        self.assertEqual(game.get_current_player().uid, "p1")
        pot = game.state.pot

        game._register_player_action(
            players["p1"],
            PlayerAction(player_uid="p1", action_type=ActionType.ALL_IN),
        )

        self.assertEqual(game.state.pot, pot + 15)
        self.assertEqual(game.state.current_bet, 20)
        state = game.get_player_snapshot("p1").state
        self.assertEqual(state.state_type, PlayerStateType.ALL_IN)
        self.assertEqual(state.stack, 0)

    def test_acting_out_of_turn_is_rejected(self):
        game, players = _game_after_blinds({"p1": 1000, "p2": 1000, "p3": 1000})
        self.assertEqual(game.get_current_player().uid, "p1")
        with self.assertRaisesRegex(ValueError, "Not this player's turn"):
            game._register_player_action(
                players["p2"],
                PlayerAction(player_uid="p2", action_type=ActionType.CALL),
            )


class TestSplitPot(unittest.TestCase):
    def test_odd_chip_goes_to_the_first_winner_after_the_button(self):
        game, players = _game_after_blinds({"p1": 1000, "p2": 1000, "p3": 1000})
        # p1 folded after putting in 5, p2 and p3 put in 10 each and tie, so the
        # first segment of 15 chips doesn't split evenly
        contributed = {"p1": 5, "p2": 10, "p3": 10}
        holdings = {
            "p1": _holding((Suit.CLUBS, Rank.FOUR), (Suit.DIAMONDS, Rank.FIVE)),
            "p2": _holding((Suit.HEARTS, Rank.TWO), (Suit.DIAMONDS, Rank.THREE)),
            "p3": _holding((Suit.CLUBS, Rank.TWO), (Suit.HEARTS, Rank.THREE)),
        }
        for uid, amount in contributed.items():
            game._update_player_state(
                players[uid],
                stack=1000 - amount,  # no chips are created or lost
                current_bet=0,
                total_contributed=amount,
                holding=holdings[uid],
                state_type=(
                    PlayerStateType.FOLDED if uid == "p1" else PlayerStateType.ACTIVE
                ),
            )
        game._update_state(
            stage=GameStage.SHOWDOWN,
            community_cards=tuple(ROYAL_FLUSH),
            pot=sum(contributed.values()),
            button_position=0,
        )

        game._handle_showdown()

        stacks = {uid: game.get_player_snapshot(uid).state.stack for uid in players}
        # 15 = 7 + 7 + 1, then 10 = 5 + 5; p2 sits first after the button
        self.assertEqual(stacks, {"p1": 995, "p2": 1003, "p3": 1002})
        self.assertEqual(game.state.pot, 0)


class TestHoldingStrength(unittest.TestCase):
    def test_complete_board_deals_no_community_cards(self):
        holding = [
            Card(suit=Suit.HEARTS, rank=Rank.TWO),
            Card(suit=Suit.DIAMONDS, rank=Rank.THREE),
        ]
        # with a royal flush on the board, every simulation is a tie, which counts
        # as a win
        strength = estimate_holding_strength(
            holding, community_cards=ROYAL_FLUSH, n_simulations=20, n_players=3
        )
        self.assertEqual(strength, 1.0)


if __name__ == "__main__":
    unittest.main()
