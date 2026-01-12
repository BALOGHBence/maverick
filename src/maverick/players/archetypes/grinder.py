from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction
from ...utils import estimate_holding_strength, find_highest_scoring_hand

if TYPE_CHECKING:
    from ...game import Game

__all__ = ["GrinderBot"]


class GrinderBot(Player):
    """A volume-oriented bot focused on steady expected value.

    Uses hand strength evaluation to make disciplined, long-term EV decisions.
    Calculates pot odds precisely and makes mathematically sound plays based on
    hand equity. Consistent bet sizing and no fancy play syndrome.

    - **Key Traits:** Multitabling, consistent lines, bankroll discipline, uses hand equity for EV calculations.
    - **Strengths:** Reliable long-term profits, disciplined decision making.
    - **Weaknesses:** Predictability, limited creativity.
    - **Common At:** Online cash games.
    """

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Play solid, consistent poker focused on long-term EV using hand strength."""
        # Evaluate hand strength
        private_cards = self.state.holding.cards
        community_cards = game.state.community_cards
        
        # Get hand equity
        if community_cards:
            hand_equity = estimate_holding_strength(
                private_cards,
                community_cards=community_cards,
                n_min_private=0,
                n_simulations=600,
                n_players=len(game.state.get_players_in_hand()),
            )
        else:
            # Pre-flop estimation
            hand_equity = estimate_holding_strength(
                private_cards,
                n_simulations=250,
                n_players=len(game.state.get_players_in_hand()),
            )

        # Grinder thresholds - focused on +EV plays
        value_hand = hand_equity > 0.60
        profitable_hand = hand_equity > 0.45

        # Standard raises for value
        if ActionType.RAISE in valid_actions and value_hand:
            raise_amount = min(min_raise, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_amount
            )

        # Bet for value with standard sizing
        if ActionType.BET in valid_actions and value_hand:
            bet_amount = min(game.state.big_blind * 2, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Call with good pot odds and profitable hands
        if ActionType.CALL in valid_actions and profitable_hand:
            call_amount = game.state.current_bet - self.state.current_bet
            # Basic pot odds calculation - call if getting 2:1 or better
            if call_amount <= self.state.stack and call_amount <= game.state.pot * 0.5:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL, amount=call_amount
                )

        # Check when free
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Fold marginal situations
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
