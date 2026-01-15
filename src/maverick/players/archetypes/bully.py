from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction
from ...utils import estimate_holding_strength

if TYPE_CHECKING:  # pragma: no cover
    from ...game import Game

__all__ = ["BullyBot"]


class BullyBot(Player):
    """A bot that uses stack size and intimidation to control the table.

    Uses hand strength evaluation to identify when to apply maximum pressure with
    large bets. Leverages hand equity to make calculated intimidation plays and
    pressure opponents with overbets when ahead.

    - **Key Traits:** Overbets, fast actions, pressure plays, uses hand strength for intimidation.
    - **Strengths:** Exploits fearful or inexperienced opponents, leverages hand equity.
    - **Weaknesses:** Overplays weak holdings when not disciplined.
    - **Common At:** Deep-stack live games.
    """

    def decide_action(
        self, game: "Game", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """Use stack size and hand strength to pressure opponents with big bets."""
        # Evaluate hand strength
        private_cards = self.state.holding.cards
        community_cards = game.state.community_cards

        # Get hand equity
        if community_cards:
            hand_equity = estimate_holding_strength(
                private_cards,
                community_cards=community_cards,
                n_private=game.rules.showdown.hole_cards_required,
                n_simulations=400,
                n_players=len(game.state.get_players_in_hand()),
            )
        else:
            # Pre-flop estimation
            hand_equity = estimate_holding_strength(
                private_cards,
                n_private=game.rules.showdown.hole_cards_required,
                n_simulations=200,
                n_players=len(game.state.get_players_in_hand()),
            )

        # Bully thresholds - willing to pressure with decent equity
        strong_hand = hand_equity > 0.60
        pressure_hand = hand_equity > 0.40

        # Big raises to pressure opponents when strong or decent
        if ActionType.RAISE in valid_actions and pressure_hand:
            # Overbet to intimidate - 2x minimum raise or 6x BB, whichever is larger
            # min_raise is the minimum raise-by increment
            raise_by_amount = max(min_raise * 2, game.state.big_blind * 6)
            raise_by_amount = min(raise_by_amount, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_by_amount
            )

        # Overbets to put pressure when strong
        if ActionType.BET in valid_actions and strong_hand:
            # Bully bets big - often pot-sized or more
            bet_amount = min(game.state.pot, self.state.stack)
            if bet_amount < game.state.big_blind * 2:
                bet_amount = min(game.state.big_blind * 4, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Will call to see showdown and apply pressure
        if ActionType.CALL in valid_actions:
            call_amount = game.state.current_bet - self.state.current_bet
            if (
                call_amount <= self.state.stack * 0.3
            ):  # Willing to call reasonable amounts
                return PlayerAction(player_id=self.id, action_type=ActionType.CALL)

        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
