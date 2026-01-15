from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction
from ...utils import estimate_holding_strength

if TYPE_CHECKING:  # pragma: no cover
    from ...game import Game

__all__ = ["GTOBot"]


class GTOBot(Player):
    """A bot with strategy driven by game-theory optimal solutions.

    Uses hand strength evaluation to implement balanced, theoretically sound play.
    Makes decisions based on hand equity with consistent bet sizing and balanced ranges.
    Aims to be unexploitable by mixing actions appropriately.

    - **Key Traits:** Balanced ranges, mixed strategies, uses hand equity for optimal play.
    - **Strengths:** Extremely difficult to exploit, mathematically sound.
    - **Weaknesses:** May underperform in soft, highly exploitative games.
    - **Common At:** Mid-to-high stakes online.
    """

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Play balanced, theoretically sound poker using hand strength evaluation."""
        # Evaluate hand strength
        private_cards = self.state.holding.cards
        community_cards = game.state.community_cards

        # Get hand equity
        if community_cards:
            hand_equity = estimate_holding_strength(
                private_cards,
                community_cards=community_cards,
                n_private=game.rules.showdown.hole_cards_required,
                n_simulations=1000,
                n_players=len(game.state.get_players_in_hand()),
            )
        else:
            # Pre-flop estimation
            hand_equity = estimate_holding_strength(
                private_cards,
                n_private=game.rules.showdown.hole_cards_required,
                n_simulations=400,
                n_players=len(game.state.get_players_in_hand()),
            )

        # GTO thresholds for balanced play
        strong_hand = hand_equity > 0.65
        medium_hand = hand_equity > 0.45

        # Standard GTO bet sizing - typically 50-75% pot
        pot_bet = int(game.state.pot * 0.66)

        # Bet with balanced sizing when strong
        if ActionType.BET in valid_actions and strong_hand:
            bet_amount = min(max(pot_bet, game.state.big_blind), self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Raise with proper sizing when strong
        if ActionType.RAISE in valid_actions and strong_hand:
            # GTO raises are typically 2.5-3x the current bet
            # min_raise is the minimum raise-by increment
            call_amount = game.state.current_bet - self.state.current_bet
            # Calculate raise-to target (2x current bet), then convert to raise-by increment
            raise_to_target = game.state.current_bet * 2
            raise_by_amount = raise_to_target - self.state.current_bet
            # Ensure we meet minimum raise requirement
            raise_by_amount = max(raise_by_amount, min_raise)
            # Cap at stack
            raise_by_amount = min(raise_by_amount, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_by_amount
            )

        # Call with proper odds and medium+ hands
        if ActionType.CALL in valid_actions and medium_hand:
            call_amount = game.state.current_bet - self.state.current_bet
            # GTO calling requires proper pot odds
            if call_amount <= self.state.stack and call_amount <= game.state.pot:
                return PlayerAction(player_id=self.id, action_type=ActionType.CALL)

        # Check in balanced way
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Fold when no good option
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
