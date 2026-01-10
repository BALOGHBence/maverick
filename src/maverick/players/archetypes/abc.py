from ...player import Player
from ...enums import ActionType
from ...state import GameState
from ...playeraction import PlayerAction

__all__ = ["ABCBot"]


class ABCBot(Player):
    """A straightforward, textbook poker bot with little deviation.

    - **Key Traits:** Plays by the book, predictable patterns, solid fundamentals.
    - **Strengths:** Consistent, avoids major mistakes.
    - **Weaknesses:** Predictable, exploitable by advanced players.
    - **Common At:** Low to mid-stakes games.
    """

    def decide_action(
        self, game_state: GameState, valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Play straightforward, textbook poker."""
        # ABC player follows standard poker guidelines
        # Standard bet sizing, plays by the book

        # Check when it's free
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Standard value bet
        if ActionType.BET in valid_actions:
            # Textbook bet: 50-75% of pot or 2-3x BB
            bet_amount = min(game_state.big_blind * 2, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Standard raise
        if ActionType.RAISE in valid_actions:
            # Textbook raise: minimum raise
            raise_amount = min(min_raise, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_amount
            )

        # Call with proper pot odds
        if ActionType.CALL in valid_actions:
            call_amount = game_state.current_bet - self.state.current_bet
            # ABC calls with 3:1 pot odds or better
            if call_amount <= self.state.stack and call_amount * 3 <= game_state.pot:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL, amount=call_amount
                )

        # Fold when not getting proper odds
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
