from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction

__all__ = ["HeroCallerBot"]


class HeroCallerBot(Player):
    """A bot that calls big bets to 'keep opponents honest,' often incorrectly.

    - **Key Traits:** Calls large bets with marginal hands, suspicious of bluffs.
    - **Strengths:** Occasionally catches bluffs.
    - **Weaknesses:** Loses chips to value bets, poor risk/reward decisions.
    - **Common At:** All stakes, recreational players.
    """

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Call large bets to catch bluffs, even with marginal holdings."""
        # Hero caller's defining trait: calls big bets to catch bluffs

        # Will call even large bets
        if ActionType.CALL in valid_actions:
            call_amount = game.state.current_bet - self.state.current_bet
            # Hero caller calls even big bets (often incorrectly)
            if call_amount <= self.state.stack * 0.6:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL, amount=call_amount
                )

        # Check when possible
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Will bet sometimes but not aggressively
        if ActionType.BET in valid_actions:
            bet_amount = min(game.state.big_blind * 2, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Rarely raises
        if ActionType.RAISE in valid_actions:
            raise_amount = min(min_raise, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_amount
            )

        # Folds only when forced to
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
