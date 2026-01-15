from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction
from ...utils import estimate_holding_strength

if TYPE_CHECKING:  # pragma: no cover
    from ...game import Game

__all__ = ["ScaredMoneyBot"]


class ScaredMoneyBot(Player):
    """A bot that plays too cautiously due to being under-rolled for the stakes.

    Uses hand strength evaluation but requires extremely high equity to play.
    Even with strong hands, plays scared and folds to any significant pressure
    due to risk aversion.

    - **Key Traits:** Risk-averse, small bets, folds easily to pressure, requires premium equity.
    - **Strengths:** Survives longer, uses hand strength conservatively.
    - **Weaknesses:** Misses value opportunities, easily exploited, too scared even with strong equity.
    - **Common At:** Players playing above their bankroll.
    """

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Play scared, risk-averse poker even with good hand strength."""
        # Evaluate hand strength but be too scared to use it
        private_cards = self.state.holding.cards
        community_cards = game.state.community_cards

        # Get hand equity but still play scared
        if community_cards:
            hand_equity = estimate_holding_strength(
                private_cards,
                community_cards=community_cards,
                n_private=0,
                n_simulations=300,
                n_players=len(game.state.get_players_in_hand()),
            )
        else:
            hand_equity = estimate_holding_strength(
                private_cards,
                n_simulations=150,
                n_players=len(game.state.get_players_in_hand()),
            )

        # Scared money requires very high equity
        premium_hand = hand_equity > 0.80  # Needs near nuts to play

        # Check whenever possible (free card)
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Only calls very small amounts, even with decent equity
        if ActionType.CALL in valid_actions and premium_hand:
            call_amount = game.state.current_bet - self.state.current_bet
            # Scared money only calls tiny amounts
            if (
                call_amount <= game.state.big_blind
                and call_amount <= self.state.stack * 0.05
            ):
                return PlayerAction(player_id=self.id, action_type=ActionType.CALL)

        # Makes tiny bets when forced to bet, even with strong hands
        if ActionType.BET in valid_actions and premium_hand:
            # Min bet only
            bet_amount = min(game.state.big_blind, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Almost never raises (too scared)
        # Folds to any significant pressure
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
