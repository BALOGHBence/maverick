"""
Player protocol for Texas Hold'em poker game.

This module defines the protocol that all player implementations must follow
to participate in a Texas Hold'em poker game.
"""

from typing import TYPE_CHECKING, Optional, Protocol, runtime_checkable

from .enums import PlayerState
from .holding import Holding

if TYPE_CHECKING:
    from .game import ActionType, GameState

__all__ = ["PlayerProtocol"]


@runtime_checkable
class PlayerProtocol(Protocol):
    """
    Protocol defining the interface for a valid player implementation.

    Any class implementing this protocol can participate in a Texas Hold'em game.
    Custom player classes must implement all methods defined in this protocol.

    Attributes
    ----------
    id : Optional[str]
        Unique identifier for the player.
    name : Optional[str]
        Display name for the player.
    seat : Optional[int]
        Seat number at the table (0-indexed).
    stack : int
        Current chip count.
    holding : Optional[Holding]
        Current hole cards (None if no cards dealt).
    current_bet : int
        Amount bet in current betting round.
    total_contributed : int
        Total amount contributed to pot this hand.
    state : Optional[PlayerState]
        Current player state (ACTIVE, FOLDED, ALL_IN).
    acted_this_street : bool
        Whether player has acted in current betting round.
    """

    id: Optional[str]
    name: Optional[str]
    seat: Optional[int]
    stack: int
    holding: Optional[Holding]
    current_bet: int
    total_contributed: int
    state: Optional[PlayerState]
    acted_this_street: bool

    def decide_action(
        self, game_state: "GameState", valid_actions: list["ActionType"], min_raise: int
    ) -> tuple["ActionType", int]:
        """
        Decide what action to take given the current game state.

        Parameters
        ----------
        game_state : GameState
            Current state of the game.
        valid_actions : list[ActionType]
            List of valid actions the player can take.
        min_raise : int
            Minimum amount for a raise action.

        Returns
        -------
        tuple[ActionType, int]
            A tuple of (action_type, amount) where amount is relevant for
            BET, RAISE, CALL, and ALL_IN actions.
        """
        ...
