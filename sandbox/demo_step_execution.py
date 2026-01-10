#!/usr/bin/env python3
"""
Demonstration of step-by-step game execution.

This script shows how to use the new step() and has_events() methods
to execute a poker game one event at a time, giving you control over
the execution flow.
"""

import logging
from maverick import Game
from maverick.players import FoldBot, CallBot
from maverick.playerstate import PlayerState

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO, format="%(message)s")


def main():
    print("=" * 70)
    print("Step-by-Step Game Execution Demo")
    print("=" * 70)
    print()

    # Create a game
    game = Game(small_blind=1, big_blind=2, max_hands=1)

    # Add players
    game.add_player(FoldBot(id="p1", name="Alice", state=PlayerState(stack=50, seat=0)))
    game.add_player(CallBot(id="p2", name="Bob", state=PlayerState(stack=50, seat=1)))

    print("Game set up with 2 players")
    print(f"Initial game state: {game.state.state_type}")
    print(f"Has pending events: {game.has_events()}")
    print()

    # Initialize and queue the first event
    game._initialize_game()
    game._event_queue.append(game._event_queue.__class__.__name__)  # Just for demo
    from maverick.enums import GameEventType

    game._event_queue.clear()
    game._event_queue.append(GameEventType.GAME_STARTED)

    print("Game initialized and GAME_STARTED event queued")
    print(f"Has pending events: {game.has_events()}")
    print()

    # Process events one at a time
    event_count = 0
    print("Processing events step-by-step:")
    print("-" * 70)

    while game.step():
        event_count += 1
        print(
            f"[Event {event_count}] State: {game.state.state_type}, "
            f"Hand: {game.state.hand_number}, "
            f"More events: {game.has_events()}"
        )

        # Limit output for demo
        if event_count >= 10:
            print("... (continuing silently)")
            break

    # Process remaining events silently
    while game.step():
        event_count += 1

    print("-" * 70)
    print()
    print(f"Game completed after {event_count} events")
    print(f"Final game state: {game.state.state_type}")
    print(f"Hands played: {game.state.hand_number}")
    print(f"Has pending events: {game.has_events()}")
    print()

    print("=" * 70)
    print("Comparison: Using start() method (runs all events at once)")
    print("=" * 70)
    print()

    # Create another game using start()
    game2 = Game(small_blind=1, big_blind=2, max_hands=1)
    game2.add_player(
        FoldBot(id="p1", name="Alice", state=PlayerState(stack=50, seat=0))
    )
    game2.add_player(CallBot(id="p2", name="Bob", state=PlayerState(stack=50, seat=1)))

    print("Running game with start() method...")
    game2.start()

    print()
    print(f"Final game state: {game2.state.state_type}")
    print(f"Hands played: {game2.state.hand_number}")
    print()

    print("Both methods produce the same result, but step() gives you control!")
    print()


if __name__ == "__main__":
    main()
