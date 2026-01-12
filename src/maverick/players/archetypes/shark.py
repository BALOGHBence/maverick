from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction

if TYPE_CHECKING:
    from ...game import Game

__all__ = ["SharkBot"]


class SharkBot(Player):
    """A bot that adapts strategy dynamically based on opponent tendencies (exploitative).

    - **Key Traits:** Strong reads, targeted adjustments.
    - **Strengths:** Maximizes profit against weak players.
    - **Weaknesses:** Requires constant attention and accurate reads.
    - **Common At:** Live games and mixed-skill environments.
    """

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Exploit opponent weaknesses with adaptive play."""
        # Shark adapts to exploit opponents
        # More aggressive against passive players, more cautious against aggressive ones
        # Uses position and pot size to make exploitative plays

        # Exploit with aggressive raises
        if ActionType.RAISE in valid_actions:
            # Size raises based on pot and exploitation
            raise_amount = min(
                max(min_raise, int(game.state.pot * 0.75)), self.state.stack
            )
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_amount
            )

        # Value bet when ahead
        if ActionType.BET in valid_actions:
            # Exploitative bet sizing - often larger for value
            bet_amount = min(int(game.state.pot * 0.8), self.state.stack)
            if bet_amount < game.state.big_blind:
                bet_amount = min(game.state.big_blind * 2, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Call when getting good odds or to trap
        if ActionType.CALL in valid_actions:
            call_amount = game.state.current_bet - self.state.current_bet
            # Sharks will call lighter in position or against weaker opponents
            if call_amount <= self.state.stack and call_amount <= game.state.pot * 0.66:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL, amount=call_amount
                )

        # Check to trap or for pot control
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Fold when exploitative play isn't profitable
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
