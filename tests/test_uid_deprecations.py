"""Tests for deprecated id/player_id aliases introduced in the uid harmonization."""

import warnings
import unittest

from maverick.playeraction import PlayerAction
from maverick.events import GameEvent
from maverick.enums import ActionType, GameEventType
from maverick.players.foldbot import FoldBot
from maverick.playerstate import PlayerState


class TestPlayerUidDeprecations(unittest.TestCase):
    """Test that Player.uid is the canonical attribute and Player.id is a deprecated alias."""

    def test_player_uid_is_set(self):
        """Player.uid is the canonical instance identifier."""
        player = FoldBot(uid="my-uid", name="Bot", state=PlayerState(stack=100))
        self.assertEqual(player.uid, "my-uid")

    def test_player_uid_auto_generated(self):
        """Player.uid is auto-generated as a UUID hex string when not provided."""
        player = FoldBot(name="Bot", state=PlayerState(stack=100))
        self.assertIsNotNone(player.uid)
        self.assertIsInstance(player.uid, str)
        self.assertEqual(len(player.uid), 32)

    def test_player_id_deprecated_property(self):
        """Accessing Player.id emits a DeprecationWarning and returns uid."""
        player = FoldBot(uid="abc123", name="Bot", state=PlayerState(stack=100))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            value = player.id
        self.assertEqual(value, "abc123")
        self.assertTrue(
            any(issubclass(w.category, DeprecationWarning) for w in caught),
            "Expected DeprecationWarning when accessing Player.id",
        )
        self.assertTrue(
            any("Player.id is deprecated" in str(w.message) for w in caught)
        )

    def test_player_init_id_param_deprecated(self):
        """Passing id= to Player.__init__ emits a DeprecationWarning and sets uid."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            player = FoldBot(id="old-id", name="Bot", state=PlayerState(stack=100))
        self.assertEqual(player.uid, "old-id")
        self.assertTrue(
            any(issubclass(w.category, DeprecationWarning) for w in caught),
            "Expected DeprecationWarning when using id= parameter",
        )
        self.assertTrue(
            any("Passing id= to Player.__init__ is deprecated" in str(w.message) for w in caught)
        )

    def test_player_uid_takes_precedence_over_id(self):
        """When both uid= and id= are provided, uid= wins without a warning for uid."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            player = FoldBot(uid="uid-wins", id="id-loses", name="Bot", state=PlayerState(stack=100))
        self.assertEqual(player.uid, "uid-wins")
        # Should still warn about the deprecated id param
        self.assertTrue(
            any(issubclass(w.category, DeprecationWarning) for w in caught)
        )

    def test_to_dict_uses_uid_key(self):
        """Player.to_dict() uses 'uid' as the key."""
        player = FoldBot(uid="my-uid", name="Bot", state=PlayerState(stack=100))
        d = player.to_dict()
        self.assertIn("uid", d)
        self.assertEqual(d["uid"], "my-uid")
        self.assertNotIn("id", d)


class TestPlayerActionUidDeprecations(unittest.TestCase):
    """Test that PlayerAction.player_uid is canonical and player_id is a deprecated alias."""

    def test_player_uid_field(self):
        """PlayerAction.player_uid is the canonical field."""
        action = PlayerAction(player_uid="p1", action_type=ActionType.FOLD)
        self.assertEqual(action.player_uid, "p1")

    def test_player_id_deprecated_constructor(self):
        """Constructing with player_id= emits DeprecationWarning and sets player_uid."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            action = PlayerAction(player_id="p1", action_type=ActionType.FOLD)
        self.assertEqual(action.player_uid, "p1")
        self.assertTrue(
            any(issubclass(w.category, DeprecationWarning) for w in caught),
            "Expected DeprecationWarning when using player_id=",
        )
        self.assertTrue(
            any("PlayerAction 'player_id' parameter is deprecated" in str(w.message) for w in caught)
        )

    def test_player_id_deprecated_property(self):
        """Accessing PlayerAction.player_id emits DeprecationWarning and returns player_uid."""
        action = PlayerAction(player_uid="p1", action_type=ActionType.FOLD)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            value = action.player_id
        self.assertEqual(value, "p1")
        self.assertTrue(
            any(issubclass(w.category, DeprecationWarning) for w in caught),
            "Expected DeprecationWarning when accessing player_id property",
        )
        self.assertTrue(
            any("PlayerAction.player_id is deprecated" in str(w.message) for w in caught)
        )


class TestGameEventUidDeprecations(unittest.TestCase):
    """Test that GameEvent.player_uid is canonical and player_id is a deprecated alias."""

    def _make_event(self, **kwargs) -> GameEvent:
        return GameEvent(
            type=GameEventType.PLAYER_JOINED,
            hand_number=1,
            **kwargs,
        )

    def test_player_uid_field(self):
        """GameEvent.player_uid is the canonical field."""
        event = self._make_event(player_uid="p1")
        self.assertEqual(event.player_uid, "p1")

    def test_player_uid_none_by_default(self):
        """GameEvent.player_uid defaults to None."""
        event = self._make_event()
        self.assertIsNone(event.player_uid)

    def test_player_id_deprecated_constructor(self):
        """Constructing with player_id= emits DeprecationWarning and sets player_uid."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            event = self._make_event(player_id="p1")
        self.assertEqual(event.player_uid, "p1")
        self.assertTrue(
            any(issubclass(w.category, DeprecationWarning) for w in caught),
            "Expected DeprecationWarning when using player_id=",
        )
        self.assertTrue(
            any("GameEvent 'player_id' parameter is deprecated" in str(w.message) for w in caught)
        )

    def test_player_id_deprecated_property(self):
        """Accessing GameEvent.player_id emits DeprecationWarning and returns player_uid."""
        event = self._make_event(player_uid="p1")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            value = event.player_id
        self.assertEqual(value, "p1")
        self.assertTrue(
            any(issubclass(w.category, DeprecationWarning) for w in caught),
            "Expected DeprecationWarning when accessing player_id property",
        )
        self.assertTrue(
            any("GameEvent.player_id is deprecated" in str(w.message) for w in caught)
        )

    def test_player_id_property_none(self):
        """GameEvent.player_id property returns None when player_uid is None."""
        event = self._make_event()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            value = event.player_id
        self.assertIsNone(value)
        self.assertTrue(any(issubclass(w.category, DeprecationWarning) for w in caught))

    def test_id_deprecated_property(self):
        """Accessing GameEvent.id emits DeprecationWarning and returns uid."""
        event = self._make_event(uid="test-uid-123")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            value = event.id
        self.assertEqual(value, "test-uid-123")
        self.assertTrue(
            any(issubclass(w.category, DeprecationWarning) for w in caught),
            "Expected DeprecationWarning when accessing GameEvent.id",
        )
        self.assertTrue(
            any("GameEvent.id is deprecated" in str(w.message) for w in caught)
        )

    def test_id_deprecated_property_matches_uid(self):
        """GameEvent.id and GameEvent.uid return the same value."""
        event = self._make_event()
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            id_value = event.id
        self.assertEqual(id_value, event.uid)


if __name__ == "__main__":
    unittest.main()
