"""
Player protocol for Texas Hold'em poker game.

This module defines the protocol that all player implementations must follow
to participate in a Texas Hold'em poker game.
"""

from typing import TYPE_CHECKING, Optional, Protocol, runtime_checkable

from .enums import ActionType
from .playeraction import PlayerAction

if TYPE_CHECKING:
    from .game import GameState
    from .playerstate import PlayerState

__all__ = ["PlayerLike"]


@runtime_checkable
class PlayerLike(Protocol):
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
    state : Optional[PlayerState]
        Current player state containing seat, stack, holding, bets, etc.
    """

    id: Optional[str]
    name: Optional[str]
    state: Optional["PlayerState"]

    def decide_action(
        self, game_state: "GameState", valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
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
        PlayerAction
            An instance of PlayerAction representing the chosen action.
        """
        ...
