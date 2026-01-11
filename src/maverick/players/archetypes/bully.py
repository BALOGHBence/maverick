from ...player import Player
from ...enums import ActionType
from ...state import GameState
from ...playeraction import PlayerAction

__all__ = ["BullyBot"]


class BullyBot(Player):
    """A bot that uses stack size and intimidation to control the table.

    - **Key Traits:** Overbets, fast actions, pressure plays.
    - **Strengths:** Exploits fearful or inexperienced opponents.
    - **Weaknesses:** Overplays weak holdings.
    - **Common At:** Deep-stack live games.
    """

    def decide_action(
        self, game_state: GameState, valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Use stack size to pressure opponents with big bets."""
        # Bully plays based on stack advantage
        # More aggressive when having a bigger stack relative to pot

        # Big raises to pressure opponents
        if ActionType.RAISE in valid_actions:
            # Overbet to intimidate - 4-6x typical
            raise_amount = min(
                max(min_raise * 2, game_state.big_blind * 6), self.state.stack
            )
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_amount
            )

        # Overbets to put pressure
        if ActionType.BET in valid_actions:
            # Bully bets big - often pot-sized or more
            bet_amount = min(game_state.pot, self.state.stack)
            if bet_amount < game_state.big_blind * 2:
                bet_amount = min(game_state.big_blind * 4, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Will call to see showdown and apply pressure
        if ActionType.CALL in valid_actions:
            call_amount = game_state.current_bet - self.state.current_bet
            if (
                call_amount <= self.state.stack * 0.3
            ):  # Willing to call reasonable amounts
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL, amount=call_amount
                )

        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
