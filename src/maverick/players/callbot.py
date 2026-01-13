from typing import TYPE_CHECKING

from ..player import Player
from ..enums import ActionType
from ..playeraction import PlayerAction

if TYPE_CHECKING:
    from ..game import Game

__all__ = ["CallBot"]


class CallBot(Player):
    """A passive bot that always calls or checks."""

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Always call or check if possible, otherwise fold."""
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)
        elif ActionType.CALL in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CALL)
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
