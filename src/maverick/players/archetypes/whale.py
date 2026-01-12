from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction

if TYPE_CHECKING:
    from ...game import Game

__all__ = ["WhaleBot"]


class WhaleBot(Player):
    """An extremely loose bot willing to gamble large sums.

    Uses hand strength evaluation but loves action and gambles anyway. Understands
    equity but the thrill of gambling overrides mathematical considerations. Makes
    huge bets regardless of hand strength.

    - **Key Traits:** Plays almost every hand, makes huge bets, gamblers mentality,
      ignores hand strength for action.
    - **Strengths:** Creates action, unpredictable, knows equity but doesn't care.
    - **Weaknesses:** Loses money quickly, plays too many weak hands despite knowing better.
    - **Common At:** High-stakes games, recreational millionaires.
    """

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Play extremely loose and gamble with large sums, using hand strength minimally."""
        # NOTE: WhaleBot doesn't rely on hand strength estimation. In fact it doesn't
        # even look at the cards at all. It loves action more than equity and plays everything.

        # Raise big - whale loves to gamble
        if ActionType.RAISE in valid_actions:
            # Huge raises
            raise_amount = min(max(min_raise * 3, game.state.pot), self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_amount
            )

        # Big bets
        if ActionType.BET in valid_actions:
            # Whale bets big
            bet_amount = min(game.state.pot, self.state.stack)
            if bet_amount < game.state.big_blind * 3:
                bet_amount = min(game.state.big_blind * 5, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Calls everything (loves action)
        if ActionType.CALL in valid_actions:
            call_amount = game.state.current_bet - self.state.current_bet
            if call_amount <= self.state.stack:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL, amount=call_amount
                )

        # Even all-in doesn't scare a whale
        if ActionType.ALL_IN in valid_actions:
            return PlayerAction(
                player_id=self.id,
                action_type=ActionType.ALL_IN,
                amount=self.state.stack,
            )

        # Check if must
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Rarely folds
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
