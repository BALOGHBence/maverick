from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction
from ...utils import estimate_holding_strength

if TYPE_CHECKING:
    from ...game import Game

__all__ = ["LoosePassiveBot"]


class LoosePassiveBot(Player):
    """A bot that plays too many hands and calls too often (calling station).

    Uses hand strength evaluation but still calls with weak equity. Understands
    pot odds in theory but applies them poorly, calling with insufficient equity
    and playing passively even with strong hands.

    - **Key Traits:** Limping, calling with weak or marginal hands, uses hand strength poorly.
    - **Strengths:** Pays off strong hands, occasionally has hand equity on their side.
    - **Weaknesses:** Long-term losing style, calls with insufficient equity.
    - **Common At:** Casual home games and low-stakes casinos.
    """

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Call frequently with many hands using hand strength poorly, rarely raise."""
        # Evaluate hand strength but still play badly
        private_cards = self.state.holding.cards
        community_cards = game.state.community_cards
        
        # Get hand equity but still call too much
        if community_cards:
            hand_equity = estimate_holding_strength(
                private_cards,
                community_cards=community_cards,
                n_min_private=0,
                n_simulations=200,
                n_players=len(game.state.get_players_in_hand()),
            )
        else:
            # Pre-flop estimation
            hand_equity = estimate_holding_strength(
                private_cards,
                n_simulations=100,
                n_players=len(game.state.get_players_in_hand()),
            )

        # Loose passive has terrible standards - evaluates but doesn't use properly

        # Check when possible
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Call almost anything, even with weak equity
        if ActionType.CALL in valid_actions:
            call_amount = game.state.current_bet - self.state.current_bet
            # Call as long as we have chips (calling station behavior)
            if call_amount <= self.state.stack:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL, amount=call_amount
                )

        # Rarely bet, but will if no one else has
        if ActionType.BET in valid_actions:
            bet_amount = min(game.state.big_blind, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Almost never raise (not aggressive)
        # Fold only when can't call
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
