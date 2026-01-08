from ..player import Player
from ..enums import ActionType
from ..state import GameState

__all__ = ["FoldBot"]


class FoldBot(Player):
    """A passive bot that always folds when possible."""

    def decide_action(
        self, game_state: GameState, valid_actions: list[ActionType], min_raise: int
    ) -> tuple[ActionType, int]:
        """Always call or check if possible, otherwise fold."""
        if ActionType.FOLD in valid_actions:
            return (ActionType.FOLD, 0)
        elif ActionType.CHECK in valid_actions:
            return (ActionType.CHECK, 0)
