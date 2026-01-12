from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction

__all__ = ["TightPassiveBot"]


class TightPassiveBot(Player):
    """A bot that plays very few hands and avoids big pots without premium holdings.

    - **Key Traits:** Folding, calling instead of raising.
    - **Strengths:** Minimizes losses.
    - **Weaknesses:** Misses value, extremely readable.
    - **Common At:** Low-stakes live games.
    """

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Play passively, avoiding raises and large bets."""
        # Check is always preferred when free
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Call only if the amount is small relative to the pot
        if ActionType.CALL in valid_actions:
            call_amount = game.state.current_bet - self.state.current_bet
            # Only call if it's less than 10% of stack and pot is worth it
            if call_amount <= self.state.stack * 0.1:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL, amount=call_amount
                )

        # Fold in most other situations (never raises or bets)
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
