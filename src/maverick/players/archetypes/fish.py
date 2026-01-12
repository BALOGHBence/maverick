from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction

if TYPE_CHECKING:
    from ...game import Game

__all__ = ["FishBot"]


class FishBot(Player):
    """A generally weak or inexperienced bot that makes systematic, exploitable mistakes.

    - **Key Traits:** Plays too many hands, poor position awareness, excessive calling, inconsistent bet sizing.
    - **Strengths:** Unpredictable in the short term.
    - **Weaknesses:** Negative expected value over time.
    - **Typical Thought:** *"Maybe this will work."*
    - **Common At:** Low-stakes online games, casual live games.
    """

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Make exploitable mistakes characteristic of weak players."""
        # Fish makes poor decisions - plays too many hands, calls too much
        # Inconsistent sizing, poor understanding of pot odds

        # Calls too much (the fish's signature move)
        if ActionType.CALL in valid_actions:
            call_amount = game.state.current_bet - self.state.current_bet
            # Fish calls with bad odds
            if call_amount <= self.state.stack * 0.4:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL, amount=call_amount
                )

        # Check when possible (passive)
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Occasionally bets with weird sizing
        if ActionType.BET in valid_actions:
            # Inconsistent sizing - sometimes min bet
            bet_amount = min(game.state.big_blind, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Rarely raises (not aggressive enough)
        if ActionType.RAISE in valid_actions:
            # Weak raises when does raise
            raise_amount = min(min_raise, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_amount
            )

        # Folds when can't call
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
