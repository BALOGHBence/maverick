from ..player import Player
from ..enums import ActionType
from ..playeraction import PlayerAction

__all__ = ["FoldBot"]


class FoldBot(Player):
    """A passive bot that always folds when possible."""

    def decide_action(self, *, valid_actions: list[ActionType], **_) -> PlayerAction:
        """Always call or check if possible, otherwise fold."""
        if ActionType.FOLD in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
        elif ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)
        assert False, "FoldBot has no valid actions to take."
