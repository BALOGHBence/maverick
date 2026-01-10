from ..player import Player
from ..enums import ActionType
from ..state import GameState
from ..playeraction import PlayerAction

__all__ = ["AggressiveBot"]


class AggressiveBot(Player):
    """An aggressive bot that frequently bets and raises."""

    def decide_action(
        self,
        game_state: GameState,
        valid_actions: list[ActionType],
        min_raise: int
    ) -> PlayerAction:
        """Bet or raise aggressively."""
        # Try to raise if possible
        if ActionType.RAISE in valid_actions:
            raise_amount = min_raise
            if raise_amount <= self.stack:
                return PlayerAction(player_id=self.id, action_type=ActionType.RAISE, amount=raise_amount)

        # Otherwise bet if possible
        if ActionType.BET in valid_actions:
            bet_amount = game_state.big_blind * 2
            if bet_amount <= self.stack:
                return PlayerAction(player_id=self.id, action_type=ActionType.BET, amount=bet_amount)

        # Call if we can't bet/raise
        if ActionType.CALL in valid_actions:
            call_amount = game_state.current_bet - self.current_bet
            if call_amount <= self.stack:
                return PlayerAction(player_id=self.id, action_type=ActionType.CALL, amount=call_amount)

        # Check if possible
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)
        
        # Otherwise fold
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)