from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction
from ...utils import estimate_holding_strength

if TYPE_CHECKING:
    from ...game import Game

__all__ = ["TightPassiveBot"]


class TightPassiveBot(Player):
    """A bot that plays very few hands and avoids big pots without premium holdings.

    Uses hand strength evaluation but plays passively even with strong hands.
    Requires very high equity to get involved and still prefers calling over raising
    even when ahead.

    - **Key Traits:** Folding, calling instead of raising, requires premium equity to play.
    - **Strengths:** Minimizes losses, uses hand strength conservatively.
    - **Weaknesses:** Misses value, extremely readable, too passive with strong hands.
    - **Common At:** Low-stakes live games.
    """

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Play passively, avoiding raises and large bets even with good equity."""
        # Evaluate hand strength but still play too passively
        private_cards = self.state.holding.cards
        community_cards = game.state.community_cards

        # Get hand equity but require premium to play
        if community_cards:
            hand_equity = estimate_holding_strength(
                private_cards,
                community_cards=community_cards,
                n_min_private=0,
                n_simulations=400,
                n_players=len(game.state.get_players_in_hand()),
            )
        else:
            # Pre-flop estimation
            hand_equity = estimate_holding_strength(
                private_cards,
                n_simulations=200,
                n_players=len(game.state.get_players_in_hand()),
            )

        # Tight passive requires very strong equity
        strong_hand = hand_equity > 0.60

        # Check is always preferred when free
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Call only if the amount is small relative to the pot and hand is strong
        if ActionType.CALL in valid_actions and strong_hand:
            call_amount = game.state.current_bet - self.state.current_bet
            # Only call if it's less than 10% of stack and pot is worth it
            if call_amount <= self.state.stack * 0.1:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL
                )

        # Fold in most other situations (never raises or bets, even with premium)
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
