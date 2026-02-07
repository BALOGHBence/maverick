"""Test to reproduce the showdown bug with no eligible players for pot segment."""

from maverick import Game
from maverick.players import CallBot


def test_showdown_all_contributors_folded():
    """
    Test scenario where all players who contributed to a pot segment have folded.
    
    This reproduces the bug: RuntimeError: No eligible players for a pot segment.
    
    Scenario:
    - 3 players
    - Player 1 posts SB (10)
    - Player 2 posts BB (20)  
    - Player 3 raises to 40
    - Player 1 folds (contributed 10)
    - Player 2 calls (now contributed 40)
    - Flop, turn, river
    - Player 3 bets, Player 2 calls
    - At showdown, contribution_levels = [10, 40, ...]
    - For level=10: segment_contributors = [P1, P2, P3]
    - But P1 folded, so eligible = [P2, P3] - this should work
    
    The bug must involve a more complex scenario...
    """
    players = [
        CallBot(id=1, name="Player1", initial_stack=1000),
        CallBot(id=2, name="Player2", initial_stack=1000),
        CallBot(id=3, name="Player3", initial_stack=1000),
    ]
    
    game = Game(players=players, small_blind=10, big_blind=20)
    
    try:
        # This should not crash
        game.start()
    except RuntimeError as e:
        if "No eligible players for a pot segment" in str(e):
            print(f"Bug reproduced: {e}")
            raise
        else:
            raise


def test_showdown_complex_scenario():
    """
    More complex scenario that might trigger the bug.
    
    What if:
    - Player posts blinds/antes
    - Player goes all-in
    - Player gets eliminated
    - Their contributions remain in the pot
    - But they're not in self.state.players anymore!
    
    This could cause segment_contributors to include eliminated players
    who are not in players_in_hand.
    """
    players = [
        CallBot(id=i, name=f"Player{i}", initial_stack=100 if i <= 2 else 1000)
        for i in range(1, 6)
    ]
    
    game = Game(players=players, small_blind=10, big_blind=20)
    
    try:
        game.start()
    except RuntimeError as e:
        if "No eligible players for a pot segment" in str(e):
            print(f"Bug reproduced with complex scenario: {e}")
            raise
        else:
            raise


if __name__ == "__main__":
    print("Test 1: Basic showdown scenario")
    try:
        test_showdown_all_contributors_folded()
        print("✓ Test 1 passed")
    except Exception as e:
        print(f"✗ Test 1 failed: {e}")
    
    print("\nTest 2: Complex scenario with eliminations")
    try:
        test_showdown_complex_scenario()
        print("✓ Test 2 passed")
    except Exception as e:
        print(f"✗ Test 2 failed: {e}")
