from ...player import Player
from ...enums import ActionType
from ...state import GameState
from ...playeraction import PlayerAction

__all__ = ["TightAggressiveBot"]


class TightAggressiveBot(Player):
    """A bot that is selective with starting hands, but bets and raises assertively when involved.
    
    - **Key Traits:** Discipline, strong value betting, positional awareness.
    - **Strengths:** Consistently profitable, difficult to exploit.
    - **Weaknesses:** Can become predictable if overly rigid.
    - **Common At:** Winning regulars in cash games and tournaments.
    """

    def decide_action(
        self, game_state: GameState, valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Always call or check if possible, otherwise fold."""
        # [COPILOT]: Implement tight-aggressive strategy here
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
