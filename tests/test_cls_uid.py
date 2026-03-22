import unittest

from maverick import Player, PlayerState
from maverick.players import (
    FoldBot,
    CallBot,
    AggressiveBot,
    TightAggressiveBot,
    LooseAggressiveBot,
    TightPassiveBot,
    LoosePassiveBot,
    ManiacBot,
    TiltedBot,
    BullyBot,
    GrinderBot,
    GTOBot,
    SharkBot,
    FishBot,
    ABCBot,
    HeroCallerBot,
    ScaredMoneyBot,
    WhaleBot,
)


class TestClsUid(unittest.TestCase):
    """Test cls_uid functionality for player classes."""

    def test_all_player_classes_have_cls_uid(self) -> None:
        """Test that all player classes have a cls_uid attribute."""
        player_classes = [
            FoldBot,
            CallBot,
            AggressiveBot,
            TightAggressiveBot,
            LooseAggressiveBot,
            TightPassiveBot,
            LoosePassiveBot,
            ManiacBot,
            TiltedBot,
            BullyBot,
            GrinderBot,
            GTOBot,
            SharkBot,
            FishBot,
            ABCBot,
            HeroCallerBot,
            ScaredMoneyBot,
            WhaleBot,
        ]

        for player_class in player_classes:
            with self.subTest(player_class=player_class.__name__):
                self.assertIsNotNone(
                    player_class.cls_uid,
                    f"{player_class.__name__} should have a cls_uid",
                )
                self.assertIsInstance(
                    player_class.cls_uid,
                    str,
                    f"{player_class.__name__}.cls_uid should be a string",
                )
                self.assertEqual(
                    len(player_class.cls_uid),
                    32,
                    f"{player_class.__name__}.cls_uid should be 32 characters long (uuid4 hex)",
                )

    def test_cls_uid_uniqueness(self) -> None:
        """Test that all cls_uid values are unique."""
        player_classes = [
            FoldBot,
            CallBot,
            AggressiveBot,
            TightAggressiveBot,
            LooseAggressiveBot,
            TightPassiveBot,
            LoosePassiveBot,
            ManiacBot,
            TiltedBot,
            BullyBot,
            GrinderBot,
            GTOBot,
            SharkBot,
            FishBot,
            ABCBot,
            HeroCallerBot,
            ScaredMoneyBot,
            WhaleBot,
        ]

        uids = [cls.cls_uid for cls in player_classes]
        self.assertEqual(
            len(uids), len(set(uids)), "All cls_uid values should be unique"
        )

    def test_get_by_uid_returns_correct_class(self) -> None:
        """Test that Player.get_by_uid returns the correct class."""
        # Test a few specific player classes
        self.assertIs(Player.get_by_uid(FoldBot.cls_uid), FoldBot)
        self.assertIs(Player.get_by_uid(CallBot.cls_uid), CallBot)
        self.assertIs(Player.get_by_uid(AggressiveBot.cls_uid), AggressiveBot)
        self.assertIs(Player.get_by_uid(TightAggressiveBot.cls_uid), TightAggressiveBot)
        self.assertIs(Player.get_by_uid(ABCBot.cls_uid), ABCBot)
        self.assertIs(Player.get_by_uid(WhaleBot.cls_uid), WhaleBot)

    def test_get_by_uid_returns_none_for_invalid_uid(self) -> None:
        """Test that Player.get_by_uid returns None for an invalid uid."""
        result = Player.get_by_uid("invalid-uid-that-does-not-exist")
        self.assertIsNone(result)

    def test_get_by_uid_can_instantiate_class(self) -> None:
        """Test that classes retrieved by uid can be instantiated."""
        player_class = Player.get_by_uid(CallBot.cls_uid)
        self.assertIsNotNone(player_class)

        # Instantiate the class
        player = player_class(
            id="test", name="TestPlayer", state=PlayerState(stack=1000, seat=0)
        )
        self.assertIsInstance(player, CallBot)
        self.assertEqual(player.name, "TestPlayer")
        self.assertEqual(player.id, "test")

    def test_all_players_retrievable_by_uid(self) -> None:
        """Test that all player classes can be retrieved by their cls_uid."""
        player_classes = [
            FoldBot,
            CallBot,
            AggressiveBot,
            TightAggressiveBot,
            LooseAggressiveBot,
            TightPassiveBot,
            LoosePassiveBot,
            ManiacBot,
            TiltedBot,
            BullyBot,
            GrinderBot,
            GTOBot,
            SharkBot,
            FishBot,
            ABCBot,
            HeroCallerBot,
            ScaredMoneyBot,
            WhaleBot,
        ]

        for player_class in player_classes:
            with self.subTest(player_class=player_class.__name__):
                retrieved_class = Player.get_by_uid(player_class.cls_uid)
                self.assertIs(
                    retrieved_class,
                    player_class,
                    f"Player.get_by_uid should return {player_class.__name__}",
                )


if __name__ == "__main__":
    unittest.main()
