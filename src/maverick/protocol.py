"""
Player protocol for Texas Hold'em poker game.

This module defines the protocol that all player implementations must follow
to participate in a Texas Hold'em poker game.
"""

from typing import TYPE_CHECKING, Optional, Protocol, runtime_checkable

from .enums import ActionType
from .playeraction import PlayerAction

if TYPE_CHECKING:  # pragma: no cover
    from .game import Game
    from .playerstate import PlayerState
    from .events import GameEvent

__all__ = ["PlayerLike", "EventHandler"]


@runtime_checkable
class EventHandler(Protocol):
    """A protocol defining the signature for event handler callables."""

    def __call__(
        self, event: "GameEvent", game: "Game"
    ) -> None: ...  # pragma: no cover


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
        self,
        *,
        game: "Game",
        valid_actions: list[ActionType],
        min_raise_amount: int,
        call_amount: int,
        min_bet_amount: int,
    ) -> PlayerAction:  # pragma: no cover
        """
        Decide what action to take given the current game state.

        Parameters
        ----------
        game : Game
            The game instance containing the current state.
        valid_actions : list[ActionType]
            List of valid actions the player can take.
        min_raise_amount : int
            Minimum extra chips this player must add right now to complete a minimum raise.
        call_amount : int
            Amount of chips this player must add right now to call the current bet.
        min_bet_amount : int
            Minimum chips this player must add right now to make a bet.

        Returns
        -------
        PlayerAction
            An instance of PlayerAction representing the chosen action.
        """
        ...

    def to_dict(self) -> dict:  # pragma: no cover
        """
        Serialize the player to a dictionary representation.

        Returns
        -------
        dict
            A dictionary containing the player's attributes.
        """
        ...
