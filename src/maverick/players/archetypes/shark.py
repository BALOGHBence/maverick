from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction
from ...utils import estimate_holding_strength

if TYPE_CHECKING:  # pragma: no cover
    from ...game import Game

__all__ = ["SharkBot"]


class SharkBot(Player):
    """A bot that adapts strategy dynamically based on opponent tendencies (exploitative).

    Uses hand strength evaluation to identify exploitation opportunities. Makes
    aggressive plays when hand equity is strong and exploitative plays when detecting
    weakness. Adjusts bet sizing based on hand strength and pot size.

    - **Key Traits:** Strong reads, targeted adjustments, uses hand equity for exploitation.
    - **Strengths:** Maximizes profit against weak players, exploits based on hand strength.
    - **Weaknesses:** Requires constant attention and accurate reads.
    - **Common At:** Live games and mixed-skill environments.
    """

    def decide_action(
        self,
        *,
        game: "Game",
        valid_actions: list[ActionType],
        min_raise_amount: int,
        call_amount: int,
        min_bet_amount: int,
    ) -> PlayerAction:
        """Exploit opponent weaknesses with adaptive play based on hand strength."""
        # Evaluate hand strength
        private_cards = self.state.holding.cards
        community_cards = game.state.community_cards

        # Get hand equity
        if community_cards:
            hand_equity = estimate_holding_strength(
                private_cards,
                community_cards=community_cards,
                n_private=game.rules.showdown.hole_cards_required,
                n_simulations=800,
                n_players=len(game.state.get_players_in_hand()),
            )
        else:
            # Pre-flop estimation
            hand_equity = estimate_holding_strength(
                private_cards,
                n_private=game.rules.showdown.hole_cards_required,
                n_simulations=300,
                n_players=len(game.state.get_players_in_hand()),
            )

        # Shark thresholds - exploitative ranges
        strong_hand = hand_equity > 0.55
        exploitable_hand = hand_equity > 0.35  # Willing to bluff

        # Exploit with aggressive raises when strong
        if ActionType.RAISE in valid_actions and strong_hand:
            # Size raises based on pot and exploitation
            # Calculate raise-to target (75% of pot above current bet), then convert to raise-by
            raise_to_target = game.state.current_bet + int(game.state.pot * 0.75)
            raise_amount = raise_to_target - self.state.current_bet
            # Ensure we meet minimum raise requirement
            raise_amount = max(raise_amount, min_raise_amount)
            # Cap at stack
            raise_amount = min(raise_amount, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_amount
            )

        # Value bet aggressively when ahead, or bluff with some equity
        if ActionType.BET in valid_actions and (strong_hand or exploitable_hand):
            # Exploitative bet sizing - larger for value, smaller for bluffs
            if strong_hand:
                bet_amount = min(int(game.state.pot * 0.8), self.state.stack)
            else:
                bet_amount = min(int(game.state.pot * 0.5), self.state.stack)
            if bet_amount < min_bet_amount:
                bet_amount = min(min_bet_amount * 2, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Call when getting good odds or to trap
        if ActionType.CALL in valid_actions and strong_hand:
            # Sharks will call lighter in position or against weaker opponents
            if call_amount <= self.state.stack and call_amount <= game.state.pot * 0.66:
                return PlayerAction(player_id=self.id, action_type=ActionType.CALL)

        # Check to trap or for pot control
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Fold when exploitative play isn't profitable
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
