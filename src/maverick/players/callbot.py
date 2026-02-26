from ..player import Player
from ..enums import ActionType
from ..playeraction import PlayerAction

__all__ = ["CallBot"]


class CallBot(Player):
    """A passive bot that always calls or checks."""

    cls_uid = "b8fbd13c3e3248afa0e219107c38fc5a"

    def decide_action(self, *, valid_actions: list[ActionType], **_) -> PlayerAction:
        """Always call or check if possible, otherwise fold."""
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)
        elif ActionType.CALL in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CALL)
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
