from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction

if TYPE_CHECKING:
    from ...game import Game

__all__ = ["GrinderBot"]


class GrinderBot(Player):
    """A volume-oriented bot focused on steady expected value.

    - **Key Traits:** Multitabling, consistent lines, bankroll discipline.
    - **Strengths:** Reliable long-term profits.
    - **Weaknesses:** Predictability, limited creativity.
    - **Common At:** Online cash games.
    """

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Play solid, consistent poker focused on long-term EV."""
        # Grinder plays ABC poker - consistent and disciplined
        # Raises with value, calls with reasonable odds, folds marginal hands

        # Check when free
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Bet for value - standard sizing
        if ActionType.BET in valid_actions:
            bet_amount = min(game.state.big_blind * 2, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Standard raises - no fancy play
        if ActionType.RAISE in valid_actions:
            raise_amount = min(min_raise, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_amount
            )

        # Call with good pot odds
        if ActionType.CALL in valid_actions:
            call_amount = game.state.current_bet - self.state.current_bet
            # Basic pot odds calculation - call if getting 2:1 or better
            if call_amount <= self.state.stack and call_amount <= game.state.pot * 0.5:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL, amount=call_amount
                )

        # Fold marginal situations
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
