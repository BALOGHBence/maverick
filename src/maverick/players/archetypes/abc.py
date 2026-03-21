from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction
from ...utils import estimate_holding_strength

if TYPE_CHECKING:  # pragma: no cover
    from ...game import Game

__all__ = ["ABCBot"]


class ABCBot(Player):
    """A straightforward, textbook poker bot with little deviation.

    Uses hand strength evaluation and pot odds to make solid, textbook decisions.
    Makes decisions based on hand equity and proper bet sizing according to
    standard poker theory.

    - **Key Traits:** Plays by the book, predictable patterns, solid fundamentals.
    - **Strengths:** Consistent, avoids major mistakes, uses proper hand evaluation.
    - **Weaknesses:** Predictable, exploitable by advanced players.
    - **Common At:** Low to mid-stakes games.
    """

    cls_uid = "f0c69546d5c54e7d8d3f3b1e1aa21ba7"

    def decide_action(
        self,
        *,
        game: "Game",
        valid_actions: list[ActionType],
        min_raise_amount: int,
        call_amount: int,
        min_bet_amount: int,
    ) -> PlayerAction:
        """Play straightforward, textbook poker using hand strength evaluation."""
        snapshot = game.get_player_snapshot(self.uid)
        # Evaluate hand strength
        private_cards = snapshot.state.holding.cards
        community_cards = game.state.community_cards

        # Get hand equity if there are community cards
        if community_cards:
            hand_equity = estimate_holding_strength(
                private_cards,
                community_cards=community_cards,
                n_private=game.rules.showdown.hole_cards_required,
                n_simulations=500,
                n_players=len(game.state.get_players_in_hand()),
            )
        else:
            # Pre-flop estimation
            hand_equity = estimate_holding_strength(
                private_cards,
                n_private=game.rules.showdown.hole_cards_required,
                n_simulations=200,
                n_players=len(game.state.get_players_in_hand()),
            )

        # Textbook thresholds for ABC play
        strong_hand = hand_equity > 0.65
        decent_hand = hand_equity > 0.45

        # Standard value bet with strong hands
        if ActionType.BET in valid_actions and strong_hand:
            # Textbook bet: 2-3x BB
            bet_amount = min(min_bet_amount, snapshot.state.stack)
            return PlayerAction(
                player_uid=self.uid, action_type=ActionType.BET, amount=bet_amount
            )

        # Standard raise with strong hands
        if ActionType.RAISE in valid_actions and strong_hand:
            # Textbook raise: minimum raise
            raise_amount = min(min_raise_amount, snapshot.state.stack)
            return PlayerAction(
                player_uid=self.uid, action_type=ActionType.RAISE, amount=raise_amount
            )

        # Call with proper pot odds and decent hands
        if ActionType.CALL in valid_actions:
            call_amount = call_amount
            # ABC calls with 3:1 pot odds or better and decent hand
            if (
                call_amount <= snapshot.state.stack
                and call_amount * 3 <= game.state.pot
                and decent_hand
            ):
                return PlayerAction(player_uid=self.uid, action_type=ActionType.CALL)

        # Check when it's free
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_uid=self.uid, action_type=ActionType.CHECK)

        # Fold when not getting proper odds or weak hand
        return PlayerAction(player_uid=self.uid, action_type=ActionType.FOLD)
