from importlib.metadata import metadata

from .card import Card
from .deck import Deck
from .enums import (
    Suit,
    Rank,
    HandType,
    Street,
    PlayerStateType,
    GameStateType,
    ActionType,
    GameEventType,
)
from .player import Player
from .hand import Hand
from .holding import Holding
from .utils.scoring import score_hand
from .game import Game
from .state import GameState
from .protocol import PlayerLike
from .playeraction import PlayerAction
from .playerstate import PlayerState
from .events import GameEvent

__all__ = [
    "Card",
    "Deck",
    "Suit",
    "Rank",
    "HandType",
    "Street",
    "PlayerStateType",
    "Player",
    "Hand",
    "Holding",
    "score_hand",
    "Game",
    "GameState",
    "GameEventType",
    "GameStateType",
    "ActionType",
    "PlayerLike",
    "PlayerAction",
    "PlayerState",
    "GameEvent",
]

__pkg_name__ = "maverick"
__pkg_metadata__ = metadata(__pkg_name__)
__version__ = __pkg_metadata__["version"]
__description__ = __pkg_metadata__["summary"]
del __pkg_metadata__
