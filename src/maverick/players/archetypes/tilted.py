from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction

if TYPE_CHECKING:
    from ...game import Game

__all__ = ["TiltedBot"]


class TiltedBot(Player):
    """A bot that is emotionally compromised after losses or bad beats.

    - **Key Traits:** Revenge plays, poor decision-making.
    - **Strengths:** None while tilted.
    - **Weaknesses:** Severe strategic leaks.
    - **Common At:** All stakes, especially after big pots.
    """

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Make irrational, emotionally-driven decisions."""
        # Tilted players make revenge plays - aggressive but poorly thought out
        # They overbet, overvalue hands, and play too many pots

        # Often goes all-in on tilt
        if ActionType.ALL_IN in valid_actions and self.state.stack < game.state.pot * 2:
            return PlayerAction(
                player_id=self.id,
                action_type=ActionType.ALL_IN,
                amount=self.state.stack,
            )

        # Raise aggressively without much thought
        if ActionType.RAISE in valid_actions:
            # Tilt raises are often oversized
            raise_amount = min(min_raise * 3, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_amount
            )

        # Bet aggressively
        if ActionType.BET in valid_actions:
            bet_amount = min(game.state.big_blind * 4, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Call too often (chasing losses)
        if ActionType.CALL in valid_actions:
            call_amount = game.state.current_bet - self.state.current_bet
            if call_amount <= self.state.stack:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL, amount=call_amount
                )

        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
