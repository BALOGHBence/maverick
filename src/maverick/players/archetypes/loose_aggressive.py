from ...player import Player
from ...enums import ActionType, Street
from ...playeraction import PlayerAction

__all__ = ["LooseAggressiveBot"]


class LooseAggressiveBot(Player):
    """A bot that plays a wide range of hands and applies relentless pressure.

    - **Key Traits:** Frequent raises, bluffs, creative lines.
    - **Strengths:** Forces opponents into mistakes, dominates passive tables.
    - **Weaknesses:** High variance, vulnerable to strong counter-strategies.
    - **Common At:** Higher-stakes games, experienced online players.
    """

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Play aggressively with a wide range of hands."""
        # LAG player tends to raise or bet frequently
        if ActionType.RAISE in valid_actions:
            # Aggressive raises - often 3-4x the big blind or current bet
            raise_amount = min(
                max(min_raise, game.state.big_blind * 3), self.state.stack
            )
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_amount
            )

        if ActionType.BET in valid_actions:
            # Aggressive bets
            bet_amount = min(game.state.big_blind * 3, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Even when can't raise/bet, still call frequently
        if ActionType.CALL in valid_actions:
            call_amount = game.state.current_bet - self.state.current_bet
            if call_amount <= self.state.stack:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL, amount=call_amount
                )

        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Fold only as last resort
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
