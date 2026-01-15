from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction
from ...utils import estimate_holding_strength

if TYPE_CHECKING:  # pragma: no cover
    from ...game import Game

__all__ = ["HeroCallerBot"]


class HeroCallerBot(Player):
    """A bot that calls big bets to 'keep opponents honest,' often incorrectly.

    Uses hand strength evaluation but makes poor calling decisions. Overestimates
    bluff frequency and calls large bets with marginal hands even when equity suggests
    folding would be better.

    - **Key Traits:** Calls large bets with marginal hands, suspicious of bluffs,
      misuses hand strength data to justify calls.
    - **Strengths:** Occasionally catches bluffs, uses hand evaluation.
    - **Weaknesses:** Loses chips to value bets, poor risk/reward decisions despite equity info.
    - **Common At:** All stakes, recreational players.
    """

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Call large bets to catch bluffs, even with marginal holdings and weak equity."""
        # Evaluate hand strength
        private_cards = self.state.holding.cards
        community_cards = game.state.community_cards

        # Get hand equity but overvalue it
        if community_cards:
            hand_equity = estimate_holding_strength(
                private_cards,
                community_cards=community_cards,
                n_private=game.rules.showdown.hole_cards_required,
                n_simulations=300,
                n_players=len(game.state.get_players_in_hand()),
            )
        else:
            # Pre-flop estimation
            hand_equity = estimate_holding_strength(
                private_cards,
                n_private=game.rules.showdown.hole_cards_required,
                n_simulations=150,
                n_players=len(game.state.get_players_in_hand()),
            )

        # Hero caller overestimates hand strength
        marginal_hand = hand_equity > 0.20  # Calls with very weak hands

        # Will call even large bets with marginal equity (signature move)
        if ActionType.CALL in valid_actions and marginal_hand:
            call_amount = game.state.current_bet - self.state.current_bet
            # Hero caller calls even big bets (often incorrectly)
            if call_amount <= self.state.stack * 0.6:
                return PlayerAction(player_id=self.id, action_type=ActionType.CALL)

        # Check when possible
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Will bet sometimes but not aggressively
        if ActionType.BET in valid_actions:
            bet_amount = min(game.state.big_blind * 2, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Rarely raises
        if ActionType.RAISE in valid_actions:
            raise_amount = min(min_raise, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_amount
            )

        # Folds only when forced to
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
