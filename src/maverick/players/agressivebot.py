from typing import TYPE_CHECKING

from ..player import Player
from ..enums import ActionType
from ..playeraction import PlayerAction

if TYPE_CHECKING:  # pragma: no cover
    from ..game import Game

__all__ = ["AggressiveBot"]


class AggressiveBot(Player):
    """An aggressive bot that frequently bets and raises."""

    def decide_action(
        self,
        *,
        game: "Game",
        valid_actions: list[ActionType],
        min_raise_amount: int,
        min_bet_amount: int,
        **_,
    ) -> PlayerAction:
        """Bet or raise aggressively."""
        # Try to raise if possible
        if ActionType.RAISE in valid_actions:
            # Use minimum raise increment
            if min_raise_amount <= self.state.stack:
                return PlayerAction(
                    player_id=self.id,
                    action_type=ActionType.RAISE,
                    amount=min_raise_amount,
                )

        # Otherwise bet if possible
        if ActionType.BET in valid_actions:
            bet_amount = max(min_bet_amount, game.state.big_blind * 2)
            if bet_amount <= self.state.stack:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.BET, amount=bet_amount
                )

        # Call if we can't bet/raise
        if ActionType.CALL in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CALL)

        # Check if possible
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Otherwise fold
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
