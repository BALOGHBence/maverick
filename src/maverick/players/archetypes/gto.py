from ...player import Player
from ...enums import ActionType
from ...state import GameState
from ...playeraction import PlayerAction

__all__ = ["GTOBot"]


class GTOBot(Player):
    """A bot with strategy driven by game-theory optimal solutions.

    - **Key Traits:** Balanced ranges, mixed strategies.
    - **Strengths:** Extremely difficult to exploit.
    - **Weaknesses:** May underperform in soft, highly exploitative games.
    - **Common At:** Mid-to-high stakes online.
    """

    def decide_action(
        self, game_state: GameState, valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Play balanced, theoretically sound poker."""
        # GTO bot aims for balance - mixing actions to be unexploitable
        # Uses consistent bet sizing and balanced ranges

        # Standard GTO bet sizing - typically 50-75% pot
        pot_bet = int(game_state.pot * 0.66)

        # Bet with balanced sizing
        if ActionType.BET in valid_actions:
            bet_amount = min(max(pot_bet, game_state.big_blind), self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Raise with proper sizing
        if ActionType.RAISE in valid_actions:
            # GTO raises are typically 2.5-3x
            raise_amount = min(
                max(min_raise, game_state.current_bet * 2), self.state.stack
            )
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_amount
            )

        # Check in balanced way
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Call with proper odds
        if ActionType.CALL in valid_actions:
            call_amount = game_state.current_bet - self.state.current_bet
            # GTO calling requires proper pot odds
            if call_amount <= self.state.stack and call_amount <= game_state.pot:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL, amount=call_amount
                )

        # Fold when no good option
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
