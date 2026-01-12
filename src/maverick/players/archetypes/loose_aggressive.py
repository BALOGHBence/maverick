from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType, Street
from ...playeraction import PlayerAction
from ...utils import estimate_holding_strength, find_highest_scoring_hand

if TYPE_CHECKING:
    from ...game import Game

__all__ = ["LooseAggressiveBot"]


class LooseAggressiveBot(Player):
    """A bot that plays a wide range of hands and applies relentless pressure.

    Uses hand strength evaluation to identify bluffing opportunities and value betting
    spots. Plays aggressively even with marginal hands, using equity to determine when
    to apply maximum pressure.

    - **Key Traits:** Frequent raises, bluffs, creative lines, uses hand equity for aggression.
    - **Strengths:** Forces opponents into mistakes, dominates passive tables.
    - **Weaknesses:** High variance, vulnerable to strong counter-strategies.
    - **Common At:** Higher-stakes games, experienced online players.
    """

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Play aggressively with a wide range of hands using hand strength."""
        # Evaluate hand strength
        private_cards = self.state.holding.cards
        community_cards = game.state.community_cards
        
        # Get hand equity
        if community_cards:
            hand_equity = estimate_holding_strength(
                private_cards,
                community_cards=community_cards,
                n_min_private=0,
                n_simulations=500,
                n_players=len(game.state.get_players_in_hand()),
            )
        else:
            # Pre-flop estimation
            hand_equity = estimate_holding_strength(
                private_cards,
                n_simulations=200,
                n_players=len(game.state.get_players_in_hand()),
            )

        # LAG thresholds - wide ranges
        any_equity = hand_equity > 0.25  # Very loose

        # LAG player tends to raise or bet frequently, even with marginal hands
        if ActionType.RAISE in valid_actions and any_equity:
            # Aggressive raises - often 3-4x the big blind or current bet
            raise_amount = min(
                max(min_raise, game.state.big_blind * 3), self.state.stack
            )
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_amount
            )

        if ActionType.BET in valid_actions and any_equity:
            # Aggressive bets
            bet_amount = min(game.state.big_blind * 3, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Even when can't raise/bet, still call frequently
        if ActionType.CALL in valid_actions:
            call_amount = game.state.current_bet - self.state.current_bet
            if call_amount <= self.state.stack:
                return PlayerAction(
                    player_id=self.id, action_type=ActionType.CALL, amount=call_amount
                )

        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Fold only as last resort
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
