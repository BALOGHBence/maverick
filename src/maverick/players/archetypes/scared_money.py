from ...player import Player
from ...enums import ActionType
from ...state import GameState
from ...playeraction import PlayerAction

__all__ = ["ScaredMoneyBot"]


class ScaredMoneyBot(Player):
    """A bot that plays too cautiously due to being under-rolled for the stakes.

    - **Key Traits:** Risk-averse, small bets, folds easily to pressure.
    - **Strengths:** Survives longer.
    - **Weaknesses:** Misses value opportunities, easily exploited.
    - **Common At:** Players playing above their bankroll.
    """

    def decide_action(
        self, game_state: GameState, valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Play scared, risk-averse poker."""
        # Scared money avoids risk, folds to pressure

        # Check whenever possible (free card)
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Only calls very small amounts
        if ActionType.CALL in valid_actions:
            call_amount = game_state.current_bet - self.state.current_bet
            # Scared money only calls tiny amounts
            if call_amount <= game_state.big_blind and call_amount <= self.state.stack * 0.05:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL, amount=call_amount
                )

        # Makes tiny bets when forced to bet
        if ActionType.BET in valid_actions:
            # Min bet only
            bet_amount = min(game_state.big_blind, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Almost never raises (too scared)
        # Folds to any significant pressure
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
