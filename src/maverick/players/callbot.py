from ..player import Player
from ..enums import ActionType
from ..state import GameState
from ..playeraction import PlayerAction

__all__ = ["CallBot"]


class CallBot(Player):
    """A passive bot that always calls or checks."""

    def decide_action(
        self, game_state: GameState, valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Always call or check if possible, otherwise fold."""
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)
        elif ActionType.CALL in valid_actions:
            call_amount = game_state.current_bet - self.state.current_bet
            if call_amount <= self.state.stack:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL, amount=call_amount
                )
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
