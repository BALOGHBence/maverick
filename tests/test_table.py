"""Comprehensive tests for the Table class."""

import unittest

from maverick import Player, PlayerState, PlayerAction, ActionType
from maverick.table import Table
from maverick.enums import PlayerStateType


class SimpleTestPlayer(Player):
    """A simple test player for testing purposes."""

    def decide_action(
        self,
        *,
        game,
        valid_actions,
        min_raise_amount,
        call_amount,
        min_bet_amount,
    ) -> PlayerAction:
        return PlayerAction(player_id=self.id, action_type=ActionType.FOLD)


class TestTableInitialization(unittest.TestCase):
    """Test Table initialization."""

    def test_table_init_with_default_seats(self):
        """Test table initialization with default number of seats."""
        table = Table()
        self.assertEqual(len(table), 9)
        self.assertIsNone(table.button_seat)
        self.assertTrue(table.has_free_seat)

    def test_table_init_with_custom_seats(self):
        """Test table initialization with custom number of seats."""
        table = Table(n_seats=6)
        self.assertEqual(len(table), 6)
        self.assertIsNone(table.button_seat)
        self.assertTrue(table.has_free_seat)

    def test_table_seats_are_initially_empty(self):
        """Test that all seats are initially None."""
        table = Table(n_seats=5)
        for i in range(5):
            self.assertIsNone(table[i])


class TestSeatPlayer(unittest.TestCase):
    """Test seating players at the table."""

    def test_seat_player_at_specific_seat(self):
        """Test seating a player at a specific seat index."""
        table = Table(n_seats=6)
        player = SimpleTestPlayer(name="Player1", state=PlayerState(stack=1000))

        seat_index = table.seat_player(player, seat_index=3)

        self.assertEqual(seat_index, 3)
        self.assertEqual(table[3], player)
        self.assertEqual(player.state.seat, 3)
        self.assertEqual(table.get_player_seat(player), 3)

    def test_seat_player_at_first_free_seat(self):
        """Test seating a player at the first available seat."""
        table = Table(n_seats=6)
        player = SimpleTestPlayer(name="Player1", state=PlayerState(stack=1000))

        seat_index = table.seat_player(player)

        self.assertEqual(seat_index, 0)
        self.assertEqual(table[0], player)
        self.assertEqual(player.state.seat, 0)

    def test_seat_multiple_players_auto_assign(self):
        """Test seating multiple players with auto seat assignment."""
        table = Table(n_seats=6)
        players = [
            SimpleTestPlayer(name=f"Player{i}", state=PlayerState(stack=1000))
            for i in range(3)
        ]

        for i, player in enumerate(players):
            seat_index = table.seat_player(player)
            self.assertEqual(seat_index, i)
            self.assertEqual(table[i], player)

    def test_seat_player_at_occupied_seat_raises_error(self):
        """Test that seating a player at an occupied seat raises an error."""
        table = Table(n_seats=6)
        player1 = SimpleTestPlayer(name="Player1", state=PlayerState(stack=1000))
        player2 = SimpleTestPlayer(name="Player2", state=PlayerState(stack=1000))

        table.seat_player(player1, seat_index=2)

        with self.assertRaises(ValueError) as context:
            table.seat_player(player2, seat_index=2)
        self.assertIn("already occupied", str(context.exception))

    def test_seat_player_at_out_of_bounds_seat_raises_error(self):
        """Test that seating a player at an out of bounds seat raises an error."""
        table = Table(n_seats=6)
        player = SimpleTestPlayer(name="Player1", state=PlayerState(stack=1000))

        with self.assertRaises(ValueError) as context:
            table.seat_player(player, seat_index=10)
        self.assertIn("out of bounds", str(context.exception))

        with self.assertRaises(ValueError) as context:
            table.seat_player(player, seat_index=-1)
        self.assertIn("out of bounds", str(context.exception))

    def test_seat_player_when_table_full_raises_error(self):
        """Test that seating a player when table is full raises an error."""
        table = Table(n_seats=3)
        players = [
            SimpleTestPlayer(name=f"Player{i}", state=PlayerState(stack=1000))
            for i in range(3)
        ]

        for player in players:
            table.seat_player(player)

        self.assertFalse(table.has_free_seat)

        extra_player = SimpleTestPlayer(name="Extra", state=PlayerState(stack=1000))
        with self.assertRaises(ValueError) as context:
            table.seat_player(extra_player)
        self.assertIn("No available seats", str(context.exception))


class TestRemovePlayer(unittest.TestCase):
    """Test removing players from the table."""

    def test_remove_player(self):
        """Test removing a player from the table."""
        table = Table(n_seats=6)
        player = SimpleTestPlayer(name="Player1", state=PlayerState(stack=1000))

        table.seat_player(player, seat_index=2)
        self.assertEqual(table[2], player)

        table.remove_player(player)

        self.assertIsNone(table[2])
        self.assertIsNone(player.state.seat)
        self.assertIsNone(table.get_player_seat(player))
        self.assertTrue(table.has_free_seat)

    def test_remove_player_from_out_of_bounds_seat_raises_error(self):
        """Test that removing a player with invalid seat raises an error."""
        table = Table(n_seats=6)
        player = SimpleTestPlayer(name="Player1", state=PlayerState(stack=1000))
        player.state.seat = 10

        with self.assertRaises(ValueError) as context:
            table.remove_player(player)
        self.assertIn("out of bounds", str(context.exception))


class TestGetPlayerSeat(unittest.TestCase):
    """Test getting player seat index."""

    def test_get_player_seat_returns_correct_seat(self):
        """Test that get_player_seat returns the correct seat index."""
        table = Table(n_seats=6)
        player = SimpleTestPlayer(name="Player1", state=PlayerState(stack=1000))

        table.seat_player(player, seat_index=4)

        self.assertEqual(table.get_player_seat(player), 4)

    def test_get_player_seat_returns_none_for_unseated_player(self):
        """Test that get_player_seat returns None for unseated player."""
        table = Table(n_seats=6)
        player = SimpleTestPlayer(name="Player1", state=PlayerState(stack=1000))

        self.assertIsNone(table.get_player_seat(player))


class TestButtonSeat(unittest.TestCase):
    """Test button seat management."""

    def test_set_button_seat(self):
        """Test setting the button seat."""
        table = Table(n_seats=6)
        player = SimpleTestPlayer(name="Player1", state=PlayerState(stack=1000))
        table.seat_player(player, seat_index=3)

        table.button_seat = 3

        self.assertEqual(table.button_seat, 3)

    def test_set_button_seat_at_empty_seat_raises_error(self):
        """Test that setting button at empty seat raises an error."""
        table = Table(n_seats=6)

        with self.assertRaises(ValueError) as context:
            table.button_seat = 2
        self.assertIn("Cannot place button at empty seat", str(context.exception))

    def test_set_button_seat_out_of_bounds_raises_error(self):
        """Test that setting button out of bounds raises an error."""
        table = Table(n_seats=6)
        player = SimpleTestPlayer(name="Player1", state=PlayerState(stack=1000))
        table.seat_player(player, seat_index=3)

        with self.assertRaises(ValueError) as context:
            table.button_seat = 10
        self.assertIn("out of bounds", str(context.exception))

    def test_set_button_seat_to_none(self):
        """Test setting button seat to None."""
        table = Table(n_seats=6)
        player = SimpleTestPlayer(name="Player1", state=PlayerState(stack=1000))
        table.seat_player(player, seat_index=3)

        table.button_seat = 3
        self.assertEqual(table.button_seat, 3)

        table.button_seat = None
        self.assertIsNone(table.button_seat)


class TestMoveButton(unittest.TestCase):
    """Test moving the button."""

    def test_move_button_when_none_places_at_first_occupied_seat(self):
        """Test that moving button when None places it at first occupied seat."""
        table = Table(n_seats=6)
        players = [
            SimpleTestPlayer(name=f"Player{i}", state=PlayerState(stack=1000))
            for i in range(3)
        ]

        table.seat_player(players[0], seat_index=1)
        table.seat_player(players[1], seat_index=3)
        table.seat_player(players[2], seat_index=5)

        button_seat = table.move_button()

        self.assertEqual(button_seat, 1)
        self.assertEqual(table.button_seat, 1)

    def test_move_button_to_next_occupied_seat(self):
        """Test moving button to next occupied seat."""
        table = Table(n_seats=6)
        players = [
            SimpleTestPlayer(name=f"Player{i}", state=PlayerState(stack=1000))
            for i in range(3)
        ]

        table.seat_player(players[0], seat_index=1)
        table.seat_player(players[1], seat_index=3)
        table.seat_player(players[2], seat_index=5)

        table.button_seat = 1
        button_seat = table.move_button()

        self.assertEqual(button_seat, 3)
        self.assertEqual(table.button_seat, 3)

    def test_move_button_wraps_around(self):
        """Test that moving button wraps around to beginning."""
        table = Table(n_seats=6)
        players = [
            SimpleTestPlayer(name=f"Player{i}", state=PlayerState(stack=1000))
            for i in range(3)
        ]

        table.seat_player(players[0], seat_index=1)
        table.seat_player(players[1], seat_index=3)
        table.seat_player(players[2], seat_index=5)

        table.button_seat = 5
        button_seat = table.move_button()

        self.assertEqual(button_seat, 1)
        self.assertEqual(table.button_seat, 1)

    def test_move_button_skips_empty_seats(self):
        """Test that moving button skips empty seats."""
        table = Table(n_seats=9)
        players = [
            SimpleTestPlayer(name=f"Player{i}", state=PlayerState(stack=1000))
            for i in range(3)
        ]

        table.seat_player(players[0], seat_index=0)
        table.seat_player(players[1], seat_index=5)
        table.seat_player(players[2], seat_index=8)

        table.button_seat = 0
        button_seat = table.move_button()

        self.assertEqual(button_seat, 5)

        button_seat = table.move_button()
        self.assertEqual(button_seat, 8)

        button_seat = table.move_button()
        self.assertEqual(button_seat, 0)


class TestNextOccupiedSeat(unittest.TestCase):
    """Test finding next occupied seat."""

    def test_next_occupied_seat_basic(self):
        """Test finding next occupied seat."""
        table = Table(n_seats=6)
        players = [
            SimpleTestPlayer(name=f"Player{i}", state=PlayerState(stack=1000))
            for i in range(3)
        ]

        table.seat_player(players[0], seat_index=1)
        table.seat_player(players[1], seat_index=3)
        table.seat_player(players[2], seat_index=5)

        next_seat = table.next_occupied_seat(1)
        self.assertEqual(next_seat, 3)

        next_seat = table.next_occupied_seat(3)
        self.assertEqual(next_seat, 5)

    def test_next_occupied_seat_wraps_around(self):
        """Test that next occupied seat wraps around."""
        table = Table(n_seats=6)
        players = [
            SimpleTestPlayer(name=f"Player{i}", state=PlayerState(stack=1000))
            for i in range(3)
        ]

        table.seat_player(players[0], seat_index=1)
        table.seat_player(players[1], seat_index=3)
        table.seat_player(players[2], seat_index=5)

        next_seat = table.next_occupied_seat(5)
        self.assertEqual(next_seat, 1)

    def test_next_occupied_seat_skips_empty_seats(self):
        """Test that next occupied seat skips empty seats."""
        table = Table(n_seats=9)
        players = [
            SimpleTestPlayer(name=f"Player{i}", state=PlayerState(stack=1000))
            for i in range(2)
        ]

        table.seat_player(players[0], seat_index=0)
        table.seat_player(players[1], seat_index=7)

        next_seat = table.next_occupied_seat(0)
        self.assertEqual(next_seat, 7)

    def test_next_occupied_seat_with_active_filter(self):
        """Test finding next occupied seat with active filter."""
        table = Table(n_seats=6)
        players = [
            SimpleTestPlayer(name=f"Player{i}", state=PlayerState(stack=1000))
            for i in range(3)
        ]

        table.seat_player(players[0], seat_index=1)
        table.seat_player(players[1], seat_index=3)
        table.seat_player(players[2], seat_index=5)

        players[1].state.state_type = PlayerStateType.FOLDED

        next_seat = table.next_occupied_seat(1, active=True)
        self.assertEqual(next_seat, 5)

    def test_next_occupied_seat_with_active_filter_all_folded(self):
        """Test next occupied seat when all players are folded."""
        table = Table(n_seats=6)
        players = [
            SimpleTestPlayer(name=f"Player{i}", state=PlayerState(stack=1000))
            for i in range(3)
        ]

        table.seat_player(players[0], seat_index=1)
        table.seat_player(players[1], seat_index=3)
        table.seat_player(players[2], seat_index=5)

        for player in players:
            player.state.state_type = PlayerStateType.FOLDED

        next_seat = table.next_occupied_seat(1, active=True)
        self.assertIsNone(next_seat)

    def test_next_occupied_seat_with_active_filter_wraps(self):
        """Test next occupied seat with active filter wraps around."""
        table = Table(n_seats=6)
        players = [
            SimpleTestPlayer(name=f"Player{i}", state=PlayerState(stack=1000))
            for i in range(3)
        ]

        table.seat_player(players[0], seat_index=1)
        table.seat_player(players[1], seat_index=3)
        table.seat_player(players[2], seat_index=5)

        players[0].state.state_type = PlayerStateType.ACTIVE
        players[1].state.state_type = PlayerStateType.FOLDED
        players[2].state.state_type = PlayerStateType.FOLDED

        next_seat = table.next_occupied_seat(3, active=True)
        self.assertEqual(next_seat, 1)


class TestTableIndexing(unittest.TestCase):
    """Test table indexing."""

    def test_getitem_returns_correct_player(self):
        """Test that __getitem__ returns the correct player."""
        table = Table(n_seats=6)
        player = SimpleTestPlayer(name="Player1", state=PlayerState(stack=1000))

        table.seat_player(player, seat_index=3)

        self.assertEqual(table[3], player)

    def test_getitem_returns_none_for_empty_seat(self):
        """Test that __getitem__ returns None for empty seat."""
        table = Table(n_seats=6)

        self.assertIsNone(table[2])


class TestHasFreeSeat(unittest.TestCase):
    """Test has_free_seat property."""

    def test_has_free_seat_when_empty(self):
        """Test has_free_seat returns True when table is empty."""
        table = Table(n_seats=6)
        self.assertTrue(table.has_free_seat)

    def test_has_free_seat_when_partially_filled(self):
        """Test has_free_seat returns True when table is partially filled."""
        table = Table(n_seats=6)
        player = SimpleTestPlayer(name="Player1", state=PlayerState(stack=1000))
        table.seat_player(player)

        self.assertTrue(table.has_free_seat)

    def test_has_free_seat_when_full(self):
        """Test has_free_seat returns False when table is full."""
        table = Table(n_seats=3)
        players = [
            SimpleTestPlayer(name=f"Player{i}", state=PlayerState(stack=1000))
            for i in range(3)
        ]

        for player in players:
            table.seat_player(player)

        self.assertFalse(table.has_free_seat)


if __name__ == "__main__":
    unittest.main()
