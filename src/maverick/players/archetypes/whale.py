from ...player import Player
from ...enums import ActionType
from ...state import GameState
from ...playeraction import PlayerAction

__all__ = ["WhaleBot"]


class WhaleBot(Player):
    """An extremely loose bot willing to gamble large sums.

    - **Key Traits:** Plays almost every hand, makes huge bets, gamblers mentality.
    - **Strengths:** Creates action, unpredictable.
    - **Weaknesses:** Loses money quickly, plays too many weak hands.
    - **Common At:** High-stakes games, recreational millionaires.
    """

    def decide_action(
        self, game_state: GameState, valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Play extremely loose and gamble with large sums."""
        # Whale plays almost everything and bets big

        # Raise big - whale loves to gamble
        if ActionType.RAISE in valid_actions:
            # Huge raises
            raise_amount = min(max(min_raise * 3, game_state.pot), self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_amount
            )

        # Big bets
        if ActionType.BET in valid_actions:
            # Whale bets big
            bet_amount = min(game_state.pot, self.state.stack)
            if bet_amount < game_state.big_blind * 3:
                bet_amount = min(game_state.big_blind * 5, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Calls everything (loves action)
        if ActionType.CALL in valid_actions:
            call_amount = game_state.current_bet - self.state.current_bet
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
