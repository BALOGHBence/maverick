from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction

if TYPE_CHECKING:
    from ...game import Game

__all__ = ["ManiacBot"]


class ManiacBot(Player):
    """A bot that is ultra-aggressive and unpredictable.

    - **Key Traits:** Constant betting and raising, massive bluffs.
    - **Strengths:** Creates confusion and short-term chaos.
    - **Weaknesses:** Burns chips rapidly over time.
    - **Common At:** Short bursts in live and online play.
    """

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Bet or raise aggressively at every opportunity."""
        # Always try to raise first
        if ActionType.RAISE in valid_actions:
            # Maniac raises big - 4-5x or more
            raise_amount = min(
                max(min_raise * 2, game.state.big_blind * 5), self.state.stack
            )
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_amount
            )

        # Bet aggressively
        if ActionType.BET in valid_actions:
            bet_amount = min(game.state.big_blind * 5, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Will even go all-in on marginal situations
        if ActionType.ALL_IN in valid_actions and self.state.stack <= game.state.pot:
            return PlayerAction(
                player_id=self.id,
                action_type=ActionType.ALL_IN,
                amount=self.state.stack,
            )

        # Call if can't raise or bet
        if ActionType.CALL in valid_actions:
            call_amount = game.state.current_bet - self.state.current_bet
            if call_amount <= self.state.stack:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL, amount=call_amount
                )

        # Even check is better than fold for a maniac
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
