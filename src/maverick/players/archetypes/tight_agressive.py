from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction

if TYPE_CHECKING:
    from ...game import Game

__all__ = ["TightAggressiveBot"]


class TightAggressiveBot(Player):
    """A bot that is selective with starting hands, but bets and raises assertively when involved.

    - **Key Traits:** Discipline, strong value betting, positional awareness.
    - **Strengths:** Consistently profitable, difficult to exploit.
    - **Weaknesses:** Can become predictable if overly rigid.
    - **Common At:** Winning regulars in cash games and tournaments.
    """

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Play selectively but aggressively when involved."""
        # TAG player is selective pre-flop but aggressive post-flop
        # Plays strong hands, values position, bets for value

        # Raise with strong hands
        if ActionType.RAISE in valid_actions:
            # Standard 3x raise
            raise_amount = min(
                max(min_raise, game.state.big_blind * 3), self.state.stack
            )
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_amount
            )

        # Bet for value
        if ActionType.BET in valid_actions:
            # Value bet: 2/3 pot or 2-3x BB
            bet_amount = min(
                max(int(game.state.pot * 0.66), game.state.big_blind * 2),
                self.state.stack,
            )
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Call selectively with good odds
        if ActionType.CALL in valid_actions:
            call_amount = game.state.current_bet - self.state.current_bet
            # TAG calls with proper odds (better than 3:1)
            if call_amount <= self.state.stack and call_amount * 3 <= game.state.pot:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL, amount=call_amount
                )

        # Check when free
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Fold without proper odds or weak holding
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
