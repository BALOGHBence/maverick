from collections import defaultdict

from .protocol import PlayerLike

__all__ = ["registered_players"]

registered_players: dict[str, PlayerLike] = defaultdict(lambda: None)
