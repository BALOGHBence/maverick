from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction
from ...utils import estimate_holding_strength

if TYPE_CHECKING:  # pragma: no cover
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

    cls_uid = "eae4e67da03d4aed8b90ef4f9d232df1"

    def decide_action(
        self,
        *,
        game: "Game",
        valid_actions: list[ActionType],
        min_raise_amount: int,
        call_amount: int,
        min_bet_amount: int,
    ) -> PlayerAction:
        """Play solid, consistent poker focused on long-term EV using hand strength."""
        snapshot = game.get_player_snapshot(self.uid)
        # Evaluate hand strength
        private_cards = snapshot.state.holding.cards
        community_cards = game.state.community_cards

        # Get hand equity
        if community_cards:
            hand_equity = estimate_holding_strength(
                private_cards,
                community_cards=community_cards,
                n_private=game.rules.showdown.hole_cards_required,
                n_simulations=600,
                n_players=len(game.state.get_players_in_hand()),
            )
        else:
            # Pre-flop estimation
            hand_equity = estimate_holding_strength(
                private_cards,
                n_private=game.rules.showdown.hole_cards_required,
                n_simulations=250,
                n_players=len(game.state.get_players_in_hand()),
            )

        # Grinder thresholds - focused on +EV plays
        value_hand = hand_equity > 0.60
        profitable_hand = hand_equity > 0.45

        # Standard raises for value
        if ActionType.RAISE in valid_actions and value_hand:
            raise_amount = min(min_raise_amount, snapshot.state.stack)
            return PlayerAction(
                player_uid=self.uid, action_type=ActionType.RAISE, amount=raise_amount
            )

        # Bet for value with standard sizing
        if ActionType.BET in valid_actions and value_hand:
            bet_amount = min(min_bet_amount * 2, snapshot.state.stack)
            return PlayerAction(
                player_uid=self.uid, action_type=ActionType.BET, amount=bet_amount
            )

        # Call with good pot odds and profitable hands
        if ActionType.CALL in valid_actions and profitable_hand:
            # Basic pot odds calculation - call if getting 2:1 or better
            if call_amount <= snapshot.state.stack and call_amount <= game.state.pot * 0.5:
                return PlayerAction(player_uid=self.uid, action_type=ActionType.CALL)

        # Check when free
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_uid=self.uid, action_type=ActionType.CHECK)

        # Fold marginal situations
        return PlayerAction(player_uid=self.uid, action_type=ActionType.FOLD)
