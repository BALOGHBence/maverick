#!/usr/bin/env python3
"""
Demo script showing the synchronous event dispatch system in action.

This script demonstrates:
1. Registering event handlers
2. Observing game events
3. Player-level event hooks
"""

from maverick import Game, GameEvent, GameEventType, ActionType, Player
from maverick.playeraction import PlayerAction
from maverick.playerstate import PlayerState


class SimpleBot(Player):
    """A simple bot that calls when possible, otherwise checks."""

    def decide_action(self, game, valid_actions, min_raise):
        if ActionType.CALL in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CALL)
        elif ActionType.CHECK in valid_actions:
            return PlayerAction(player_id=self.id, action_type=ActionType.CHECK)
        else:
            return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)


class ObservantPlayer(SimpleBot):
    """A player that logs events it observes."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, "event_count", 0)

    def on_event(self, event: GameEvent) -> None:
        """Track how many events this player observes."""
        # Use object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, "event_count", self.event_count + 1)


def main():
    print("=" * 60)
    print("Maverick Event System Demo")
    print("=" * 60)
    print()

    # Create a game
    game = Game(small_blind=10, big_blind=20, max_hands=1)

    # Create a global event counter
    event_counts = {event_type: 0 for event_type in GameEventType}

    def count_events(event: GameEvent):
        """Count each type of event."""
        event_counts[event.type] += 1

    def log_major_events(event: GameEvent):
        """Log major game events."""
        if event.type in [
            GameEventType.GAME_STARTED,
            GameEventType.HAND_STARTED,
            GameEventType.HAND_ENDED,
        ]:
            print(f"📢 {event.type.name} (Hand #{event.hand_number}, Street: {event.street.name})")

    def log_player_actions(event: GameEvent):
        """Log player actions with details."""
        if event.type == GameEventType.PLAYER_ACTION:
            action_str = f"{event.action.name}"
            if event.amount:
                action_str += f" ({event.amount} chips)"
            print(
                f"  🎲 Player {event.player_id}: {action_str} | "
                f"Pot: {event.pot} | Current Bet: {event.current_bet}"
            )

    def log_street_changes(event: GameEvent):
        """Log when streets change."""
        if event.type in [
            GameEventType.DEAL_FLOP,
            GameEventType.DEAL_TURN,
            GameEventType.DEAL_RIVER,
        ]:
            print(f"  🃏 {event.type.name} - Moving to {event.street.name}")

    # Register event handlers
    game.on(GameEventType.GAME_STARTED, count_events)
    game.on(GameEventType.GAME_STARTED, log_major_events)
    game.on(GameEventType.HAND_STARTED, count_events)
    game.on(GameEventType.HAND_STARTED, log_major_events)
    game.on(GameEventType.HAND_ENDED, count_events)
    game.on(GameEventType.HAND_ENDED, log_major_events)
    game.on(GameEventType.PLAYER_ACTION, count_events)
    game.on(GameEventType.PLAYER_ACTION, log_player_actions)
    game.on(GameEventType.DEAL_FLOP, count_events)
    game.on(GameEventType.DEAL_FLOP, log_street_changes)
    game.on(GameEventType.DEAL_TURN, count_events)
    game.on(GameEventType.DEAL_TURN, log_street_changes)
    game.on(GameEventType.DEAL_RIVER, count_events)
    game.on(GameEventType.DEAL_RIVER, log_street_changes)

    # Add players (one with event hook)
    p1 = SimpleBot(id="alice", name="Alice", state=PlayerState(stack=1000))
    p2 = ObservantPlayer(id="bob", name="Bob", state=PlayerState(stack=1000))
    p3 = SimpleBot(id="charlie", name="Charlie", state=PlayerState(stack=1000))

    game.add_player(p1)
    game.add_player(p2)
    game.add_player(p3)

    print(f"Added 3 players: {p1.name}, {p2.name}, {p3.name}")
    print()

    # Run the game
    print("Starting game...")
    print()
    game.start()

    print()
    print("=" * 60)
    print("Event Summary")
    print("=" * 60)
    print()

    # Print event counts
    print("Global Event Counts:")
    for event_type, count in sorted(event_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  {event_type.name:30s}: {count:3d}")

    print()
    print(f"Player-Level Event Hooks:")
    print(f"  Bob observed {p2.event_count} events through on_event() hook")

    print()
    print("=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
