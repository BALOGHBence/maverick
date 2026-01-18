from typing import TYPE_CHECKING

from ...player import Player
from ...enums import ActionType
from ...playeraction import PlayerAction
from ...utils import estimate_holding_strength

if TYPE_CHECKING:  # pragma: no cover
    from ...game import Game

__all__ = ["FishBot"]


class FishBot(Player):
    """A generally weak or inexperienced bot that makes systematic, exploitable mistakes.

    Has access to hand strength evaluation but misinterprets or ignores the information.
    Calls with weak hands, misunderstands pot odds, and makes poor decisions even
    with hand equity data available.

    - **Key Traits:** Plays too many hands, poor position awareness, excessive calling,
      inconsistent bet sizing, misuses hand strength information.
    - **Strengths:** Unpredictable in the short term.
    - **Weaknesses:** Negative expected value over time, calls with poor equity.
    - **Typical Thought:** *"Maybe this will work."*
    - **Common At:** Low-stakes online games, casual live games.
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
        """Make exploitable mistakes characteristic of weak players, misusing hand strength."""
        # Evaluate hand strength but use it poorly
        private_cards = self.state.holding.cards
        community_cards = game.state.community_cards

        # Get hand equity but often ignore it
        if community_cards:
            hand_equity = estimate_holding_strength(
                private_cards,
                community_cards=community_cards,
                n_private=game.rules.showdown.hole_cards_required,
                n_simulations=100,  # Fish doesn't spend much time thinking
                n_players=len(game.state.get_players_in_hand()),
            )
        else:
            # Pre-flop estimation
            hand_equity = estimate_holding_strength(
                private_cards,
                n_private=game.rules.showdown.hole_cards_required,
                n_simulations=50,
                n_players=len(game.state.get_players_in_hand()),
            )

        # Fish has terrible thresholds - calls with anything
        any_hand = hand_equity > 0.15  # Plays way too many hands

        # Calls too much (the fish's signature move) - ignores hand strength
        if ActionType.CALL in valid_actions:
            # Fish calls with bad odds and weak hands
            if call_amount <= self.state.stack * 0.4:
                return PlayerAction(player_id=self.id, action_type=ActionType.CALL)

        # Check when possible (passive)
        if ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)

        # Occasionally bets with weird sizing, regardless of hand strength
        if ActionType.BET in valid_actions:
            # Inconsistent sizing - sometimes min bet
            bet_amount = min(min_bet_amount, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.BET, amount=bet_amount
            )

        # Rarely raises (not aggressive enough), even with good hands
        if ActionType.RAISE in valid_actions and any_hand:
            # Weak raises when does raise
            raise_amount = min(min_raise_amount, self.state.stack)
            return PlayerAction(
                player_id=self.id, action_type=ActionType.RAISE, amount=raise_amount
            )

        # Folds when can't call
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)
