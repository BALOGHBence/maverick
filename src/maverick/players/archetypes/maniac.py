from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction

if TYPE_CHECKING:  # pragma: no cover
    from ...game import Game

__all__ = ["ManiacBot"]


class ManiacBot(Player):
    """A bot that is ultra-aggressive and unpredictable.

    Has access to hand strength evaluation but largely ignores it in favor of
    maximum aggression. Plays almost every hand aggressively regardless of equity,
    creating chaos at the table.

    - **Key Traits:** Constant betting and raising, massive bluffs, ignores hand strength.
    - **Strengths:** Creates confusion and short-term chaos.
    - **Weaknesses:** Burns chips rapidly over time, poor equity management.
    - **Common At:** Short bursts in live and online play.
    """

    def decide_action(
        self,
        *,
        game: "Game",
        valid_actions: list[ActionType],
        min_raise_amount: int,
        min_bet_amount: int,
        **_,
    ) -> PlayerAction:
        """Bet or raise aggressively at every opportunity, largely ignoring hand strength."""
        # NOTE: ManiacBot doesn't rely on hand strength estimation. In fact it doesn't
        # even look at the cards at all. It just plays everything aggressively.

        # Always try to raise first
        if ActionType.RAISE in valid_actions:
            # Maniac raises big - typically 2x minimum raise or 5x BB, whichever is larger
            # min_raise_amount is the minimum raise-by increment
            raise_by_amount = max(min_raise_amount * 2, game.state.big_blind * 5)
            raise_by_amount = min(raise_by_amount, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_by_amount
            )

        # Bet aggressively
        if ActionType.BET in valid_actions:
            bet_amount = min(min_bet_amount * 5, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Will even go all-in on marginal situations
        if (
            ActionType.ALL_IN in valid_actions
            and self.state.stack <= game.state.pot * 2
        ):
            return PlayerAction(
                player_id=self.id,
                action_type=ActionType.ALL_IN,
                amount=self.state.stack,
            )

        # Call if can't raise or bet
        if ActionType.CALL in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CALL)

        # Even check is better than fold for a maniac
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
