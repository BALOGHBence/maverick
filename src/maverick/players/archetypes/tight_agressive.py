from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction
from ...utils import estimate_holding_strength

if TYPE_CHECKING:
    from ...game import Game

__all__ = ["TightAggressiveBot"]


class TightAggressiveBot(Player):
    """A bot that is selective with starting hands, but bets and raises assertively when involved.

    Uses hand strength evaluation to make disciplined decisions. Only plays hands with
    strong equity and bets aggressively for value when ahead. Uses proper bet sizing
    based on hand strength and pot odds.

    - **Key Traits:** Discipline, strong value betting, positional awareness, uses hand equity.
    - **Strengths:** Consistently profitable, difficult to exploit, makes +EV decisions.
    - **Weaknesses:** Can become predictable if overly rigid.
    - **Common At:** Winning regulars in cash games and tournaments.
    """

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Play selectively but aggressively when involved using hand strength."""
        # Evaluate hand strength
        private_cards = self.state.holding.cards
        community_cards = game.state.community_cards

        # Get hand equity
        if community_cards:
            hand_equity = estimate_holding_strength(
                private_cards,
                community_cards=community_cards,
                n_min_private=0,
                n_simulations=800,
                n_players=len(game.state.get_players_in_hand()),
            )
        else:
            # Pre-flop estimation
            hand_equity = estimate_holding_strength(
                private_cards,
                n_simulations=300,
                n_players=len(game.state.get_players_in_hand()),
            )

        # TAG thresholds - selective but aggressive
        strong_hand = hand_equity > 0.55
        playable_hand = hand_equity > 0.40

        # Raise aggressively with strong hands
        if ActionType.RAISE in valid_actions and strong_hand:
            # Standard 3x BB or 3x minimum raise, whichever is larger
            # min_raise is the minimum raise-by increment
            raise_by_amount = max(min_raise, game.state.big_blind * 3)
            raise_by_amount = min(raise_by_amount, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_by_amount
            )

        # Bet for value with strong hands
        if ActionType.BET in valid_actions and strong_hand:
            # Value bet: 2/3 pot or 2-3x BB
            bet_amount = min(
                max(int(game.state.pot * 0.66), game.state.big_blind * 2),
                self.state.stack,
            )
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Call selectively with good odds and playable hands
        if ActionType.CALL in valid_actions and playable_hand:
            call_amount = game.state.current_bet - self.state.current_bet
            # TAG calls with proper odds (better than 3:1)
            if call_amount <= self.state.stack and call_amount * 3 <= game.state.pot:
                return PlayerAction(player_id=self.id, action_type=ActionType.CALL)

        # Check when free
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Fold without proper odds or weak holding
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
