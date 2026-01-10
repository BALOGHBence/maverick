from ...player import Player
from ...enums import ActionType
from ...state import GameState
from ...playeraction import PlayerAction

__all__ = ["LoosePassiveBot"]


class LoosePassiveBot(Player):
    """A bot that plays too many hands and calls too often (calling station).

    - **Key Traits:** Limping, calling with weak or marginal hands.
    - **Strengths:** Pays off strong hands.
    - **Weaknesses:** Long-term losing style.
    - **Common At:** Casual home games and low-stakes casinos.
    """

    def decide_action(
        self, game_state: GameState, valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Call frequently with many hands, rarely raise."""
        # Check when possible
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Call almost anything
        if ActionType.CALL in valid_actions:
            call_amount = game_state.current_bet - self.state.current_bet
            # Call as long as we have chips (calling station behavior)
            if call_amount <= self.state.stack:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL, amount=call_amount
                )

        # Rarely bet, but will if no one else has
        if ActionType.BET in valid_actions:
            bet_amount = min(game_state.big_blind, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Almost never raise (not aggressive)
        # Fold only when can't call
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
