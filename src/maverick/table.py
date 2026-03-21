from typing import Optional

from .protocol import PlayerLike

__all__ = ["Table"]


class Table:
    """Represents a poker table with seating for players.

    .. versionadded:: 0.2.0

    Parameters
    ----------
    n_seats : int, optional
        The number of seats at the table. Default is 9.

    Notes
    -----
    Seats are tracked by player UID (str). Navigation methods accept an
    optional ``active_uids`` set to restrict movement to active players.

    .. versionchanged:: 0.8.0
        ``_seats`` now stores player UIDs (``str``) instead of live player
        objects. ``seat_player`` / ``remove_player`` no longer mutate
        ``player.state``; that responsibility belongs to ``Game``.
    """

    def __init__(self, n_seats: int = 9) -> None:
        self._n_seats = n_seats
        self._seats: list[Optional[str]] = [None] * n_seats
        self._id_to_seat: dict[Optional[str], int] = {}
        self._button_seat: Optional[int] = None

    @property
    def button_seat(self) -> Optional[int]:
        """The seat index of the dealer button, or None if not set."""
        return self._button_seat

    @button_seat.setter
    def button_seat(self, seat_index: Optional[int]) -> None:
        """Set the seat index of the dealer button."""
        if seat_index is not None:
            if not (0 <= seat_index < self._n_seats):
                raise ValueError(f"Seat index {seat_index} is out of bounds.")

            if self.seats[seat_index] is None:
                raise ValueError(f"Cannot place button at empty seat {seat_index}.")

        self._button_seat = seat_index

    @property
    def seats(self) -> list[Optional[str]]:
        """List of player UIDs at each seat, or None if the seat is empty."""
        return self._seats

    @property
    def has_free_seat(self) -> bool:
        """Check if there is at least one free seat at the table."""
        return any(seat is None for seat in self.seats)

    def __getitem__(self, seat_index: int) -> Optional[str]:
        """Get the player UID at the specified seat index, or None if empty."""
        return self.seats[seat_index]

    def __len__(self) -> int:
        """Return the number of seats at the table."""
        return len(self.seats)

    def _find_free_seat(self) -> Optional[int]:
        """Find the first available seat index, or None if full."""
        for i in range(self._n_seats):
            if self.seats[i] is None:
                return i
        return None

    def seat_player(self, player: PlayerLike, seat_index: Optional[int] = None) -> int:
        """Seat a player at the specified seat index and return the seat index.

        .. versionchanged:: 0.8.0
            No longer mutates ``player.state``; seat information is managed
            exclusively through ``PlayerSnapshot`` in ``GameState``.
        """
        if seat_index is not None:
            if not (0 <= seat_index < self._n_seats):
                raise ValueError(f"Seat index {seat_index} is out of bounds.")

            if self.seats[seat_index] is not None:
                raise ValueError(f"Seat {seat_index} is already occupied.")

        else:
            seat_index = self._find_free_seat()
            if seat_index is None:
                raise ValueError("No available seats at the table.")

        self.seats[seat_index] = player.uid
        self._id_to_seat[player.uid] = seat_index

        return seat_index

    def remove_player(self, player: PlayerLike) -> None:
        """Remove a player from the table.

        .. versionchanged:: 0.8.0
            No longer mutates ``player.state``; seat information is managed
            exclusively through ``PlayerSnapshot`` in ``GameState``.
        """
        seat_index = self._id_to_seat.get(player.uid)

        if seat_index is None:
            raise ValueError(f"Player '{player.uid}' is not seated at this table.")

        if not (0 <= seat_index < self._n_seats):
            raise ValueError(f"Seat index {seat_index} is out of bounds.")  # pragma: no cover

        self.seats[seat_index] = None
        del self._id_to_seat[player.uid]

    def get_player_seat(self, player: PlayerLike) -> Optional[int]:
        """Get the seat index of the specified player, or None if not seated."""
        return self._id_to_seat.get(player.uid, None)

    def move_button(self) -> int:
        """Move the dealer button to the next occupied seat and return the new button seat index."""
        if self.button_seat is None:
            # Place button at first occupied seat
            for i in range(self._n_seats):
                if self.seats[i] is not None:
                    self.button_seat = i
                    return self.button_seat
        else:
            # Move button to next occupied seat
            start_seat = self.button_seat
            for offset in range(1, self._n_seats + 1):
                next_seat = (start_seat + offset) % self._n_seats
                if self.seats[next_seat] is not None:
                    self.button_seat = next_seat
                    return self.button_seat

        raise ValueError(
            "No players seated at the table to move the button."
        )  # pragma: no cover

    def next_occupied_seat(
        self,
        start_seat: int,
        *,
        active_uids: Optional[set] = None,
    ) -> Optional[int]:
        """Find the next occupied seat index after the specified start seat index.

        Parameters
        ----------
        start_seat : int
            The seat index to start searching from (exclusive).
        active_uids : set[str] | None, optional
            When provided, only seats whose player UID is contained in this
            set are considered. Pass the UIDs of all currently active players
            to restrict movement to active seats.

        .. versionchanged:: 0.8.0
            Replaced the ``active: bool`` parameter with ``active_uids: set``
            so that callers supply the active-player information explicitly
            (Table no longer holds live player-state references).
        """
        for offset in range(1, self._n_seats + 1):
            next_seat = (start_seat + offset) % self._n_seats
            uid = self.seats[next_seat]

            if uid is None:
                continue

            if active_uids is not None and uid not in active_uids:
                continue

            return next_seat

        return None  # pragma: no cover
