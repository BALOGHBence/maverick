from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction
from ...utils import estimate_holding_strength

if TYPE_CHECKING:
    from ...game import Game

__all__ = ["TiltedBot"]


class TiltedBot(Player):
    """A bot that is emotionally compromised after losses or bad beats.

    Uses hand strength evaluation but interprets it irrationally. Makes emotionally-
    driven decisions, overvaluing hands and making revenge plays based on poor
    emotional reasoning rather than sound equity calculations.

    - **Key Traits:** Revenge plays, poor decision-making, irrational use of hand strength.
    - **Strengths:** None while tilted.
    - **Weaknesses:** Severe strategic leaks, misuses equity information.
    - **Common At:** All stakes, especially after big pots.
    """

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Make irrational, emotionally-driven decisions using hand strength poorly."""
        # Evaluate hand strength but use it irrationally
        private_cards = self.state.holding.cards
        community_cards = game.state.community_cards
        
        # Get hand equity but overvalue everything on tilt
        if community_cards:
            hand_equity = estimate_holding_strength(
                private_cards,
                community_cards=community_cards,
                n_min_private=0,
                n_simulations=100,  # Tilted player doesn't think clearly
                n_players=len(game.state.get_players_in_hand()),
            )
        else:
            hand_equity = estimate_holding_strength(
                private_cards,
                n_simulations=50,
                n_players=len(game.state.get_players_in_hand()),
            )

        # Tilted players overvalue everything - irrational thresholds
        tilted_mindset = hand_equity > 0.20  # Thinks anything is good enough

        # Often goes all-in on tilt, even with marginal equity
        if ActionType.ALL_IN in valid_actions and self.state.stack < game.state.pot * 2 and tilted_mindset:
            return PlayerAction(
                player_id=self.id,
                action_type=ActionType.ALL_IN,
                amount=self.state.stack,
            )

        # Raise aggressively without much thought
        if ActionType.RAISE in valid_actions:
            # Tilt raises are often oversized
            raise_amount = min(min_raise * 3, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_amount
            )

        # Bet aggressively
        if ActionType.BET in valid_actions:
            bet_amount = min(game.state.big_blind * 4, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Call too often (chasing losses)
        if ActionType.CALL in valid_actions:
            call_amount = game.state.current_bet - self.state.current_bet
            if call_amount <= self.state.stack:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL, amount=call_amount
                )

        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
