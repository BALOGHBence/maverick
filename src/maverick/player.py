from typing import Optional

from pydantic import BaseModel, Field, model_validator

from .enums import ActionType, PlayerStateType
from .state import GameState
from .playeraction import PlayerAction
from .playerstate import PlayerState
from .holding import Holding

__all__ = ["Player"]


class Player(BaseModel):
    """A player's state during a poker game."""

    id: Optional[str] = None
    name: Optional[str] = None
    state: Optional[PlayerState] = None

    @model_validator(mode='before')
    @classmethod
    def create_state_from_params(cls, data):
        """
        Create PlayerState from direct parameters for backward compatibility.
        
        Allows passing stack, seat, holding, etc. directly when creating a Player,
        and automatically creates the PlayerState object.
        """
        if isinstance(data, dict):
            # If state is not provided but individual fields are
            if data.get('state') is None:
                state_fields = {}
                
                # Collect fields that belong in PlayerState
                if 'seat' in data:
                    state_fields['seat'] = data.pop('seat')
                if 'stack' in data:
                    state_fields['stack'] = data.pop('stack')
                if 'holding' in data:
                    state_fields['holding'] = data.pop('holding')
                if 'current_bet' in data:
                    state_fields['current_bet'] = data.pop('current_bet')
                if 'total_contributed' in data:
                    state_fields['total_contributed'] = data.pop('total_contributed')
                if 'acted_this_street' in data:
                    state_fields['acted_this_street'] = data.pop('acted_this_street')
                if 'state_type' in data:
                    state_fields['state_type'] = data.pop('state_type')
                
                # Create PlayerState if we have any state fields
                if state_fields:
                    data['state'] = PlayerState(**state_fields)
        
        return data

    def decide_action(
        self, game_state: GameState, valid_actions: list[ActionType], min_raise: int
    ) -> PlayerAction:
        """
        Decide on an action to take during the player's turn.

        The function should return a valid instance of PlayerAction.
        """
        raise NotImplementedError(
            "decide_action method must be implemented by subclasses."
        )
