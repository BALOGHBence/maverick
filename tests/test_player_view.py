"""Tests for the information-safe PlayerView handed to players."""

import dataclasses
import unittest
from collections.abc import Mapping

from pydantic import BaseModel

from maverick import (
    ActionType,
    Card,
    Deck,
    Game,
    GameEvent,
    GameEventType,
    GameState,
    Holding,
    Player,
    PlayerAction,
    PlayerSnapshot,
    PlayerState,
    PlayerView,
    Rank,
    Suit,
)
from maverick.playerview import EventHistoryView, redact_event, redact_state


class RecordingPlayer(Player):
    """Checks or calls, and records every view and event it receives."""

    def __init__(self, fold: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.fold = fold
        self.decision_views: list[PlayerView] = []
        self.event_views: list[tuple[GameEvent, PlayerView]] = []

    def decide_action(self, *, game, valid_actions, **_) -> PlayerAction:
        self.decision_views.append(game)
        if self.fold and ActionType.FOLD in valid_actions:
            action_type = ActionType.FOLD
        elif ActionType.CHECK in valid_actions:
            action_type = ActionType.CHECK
        else:
            action_type = ActionType.CALL
        return PlayerAction(player_uid=self.uid, action_type=action_type)

    def on_event(self, event, game) -> None:
        self.event_views.append((event, game))


def _make_game(*players: Player, max_hands: int = 1) -> Game:
    game = Game(small_blind=1, big_blind=2, max_hands=max_hands)
    for player in players:
        game.add_player(player, state=PlayerState(stack=100))
    return game


def _all_objects(root: object) -> list[object]:
    """Collect every object reachable from a view through its data."""
    seen: set[int] = set()
    found: list[object] = []
    stack = [root]
    while stack:
        obj = stack.pop()
        if id(obj) in seen or isinstance(obj, (str, bytes, int, float, bool)):
            continue
        seen.add(id(obj))
        found.append(obj)
        if dataclasses.is_dataclass(obj):
            stack.extend(getattr(obj, f.name) for f in dataclasses.fields(obj))
        elif isinstance(obj, BaseModel):
            stack.extend(getattr(obj, name) for name in type(obj).model_fields)
        elif isinstance(obj, EventHistoryView):
            stack.extend(obj)
        elif isinstance(obj, Mapping):
            stack.extend(obj.keys())
            stack.extend(obj.values())
        elif isinstance(obj, (list, tuple, set, frozenset)):
            stack.extend(obj)
    return found


def _opponent_holdings_in_dump(dump: dict, viewer_uid: str) -> list:
    return [
        p["state"]["holding"]
        for p in dump["players"]
        if p["uid"] != viewer_uid and p["state"]["holding"] is not None
    ]


class TestPlayerViewInGame(unittest.TestCase):
    def test_decide_action_receives_player_view(self):
        p1 = RecordingPlayer(uid="p1", name="P1")
        p2 = RecordingPlayer(uid="p2", name="P2")
        game = _make_game(p1, p2)
        game.start()

        self.assertTrue(p1.decision_views)
        for player in (p1, p2):
            for view in player.decision_views:
                self.assertIsInstance(view, PlayerView)
                self.assertEqual(view.player_uid, player.uid)
                self.assertEqual(view.game_uid, game.uid)
                self.assertEqual(view.uid, game.uid)

    def test_own_holding_visible_opponent_holding_hidden(self):
        p1 = RecordingPlayer(uid="p1", name="P1")
        p2 = RecordingPlayer(uid="p2", name="P2")
        game = _make_game(p1, p2)
        game.start()

        for player, opponent in ((p1, p2), (p2, p1)):
            # Only look at decisions before the showdown reveals anything
            for view in player.decision_views:
                self.assertIsNotNone(view.holding)
                self.assertEqual(view.me.state.holding, view.holding)
                self.assertIsNone(
                    view.get_player_snapshot(opponent).state.holding,
                    "opponent holding leaked into decide_action",
                )

    def test_revealed_holdings_visible_until_next_hand(self):
        p1 = RecordingPlayer(uid="p1", name="P1")
        p2 = RecordingPlayer(uid="p2", name="P2")
        game = _make_game(p1, p2, max_hands=2)
        game.start()

        reveal_hands = {
            (event.hand_number, event.player_uid)
            for event, _ in p1.event_views
            if event.type == GameEventType.PLAYER_CARDS_REVEALED
        }
        self.assertIn((1, "p2"), reveal_hands)

        revealed = False
        checked_hidden_again = False
        for event, view in p1.event_views:
            opponent = view.get_player_snapshot("p2")
            if opponent is None:  # p2 has not joined yet
                continue
            opponent_holding = opponent.state.holding
            if event.type == GameEventType.HAND_STARTED:
                revealed = False
            if (
                event.type == GameEventType.PLAYER_CARDS_REVEALED
                and event.player_uid == "p2"
            ):
                revealed = True
                self.assertIsNotNone(opponent_holding)
                self.assertEqual(
                    [c.code() for c in opponent_holding.cards],
                    event.payload["holding"],
                )
            if not revealed:
                self.assertIsNone(opponent_holding)
            if event.hand_number == 2 and event.type == GameEventType.HOLE_CARDS_DEALT:
                checked_hidden_again = True
                self.assertIsNotNone(view.holding)
                self.assertIsNone(opponent_holding)
        self.assertTrue(checked_hidden_again)

    def test_event_hooks_receive_player_view(self):
        p1 = RecordingPlayer(uid="p1", name="P1")
        p2 = RecordingPlayer(uid="p2", name="P2")
        game = _make_game(p1, p2)
        game.start()

        self.assertTrue(p1.event_views)
        for event, view in p1.event_views:
            self.assertIsInstance(view, PlayerView)
            self.assertIsInstance(event, GameEvent)
            # The hook gets the latest event of the view's history
            self.assertEqual(view.history[-1].uid, event.uid)

    def test_specific_event_hook_receives_player_view(self):
        received = []

        class HookPlayer(RecordingPlayer):
            def on_hand_started(self, event, game) -> None:
                received.append(game)

        p1 = HookPlayer(uid="p1", name="P1")
        p2 = RecordingPlayer(uid="p2", name="P2")
        game = _make_game(p1, p2)
        game.start()

        self.assertEqual(len(received), 1)
        self.assertIsInstance(received[0], PlayerView)

    def test_no_game_internals_reachable_from_view(self):
        p1 = RecordingPlayer(uid="p1", name="P1")
        p2 = RecordingPlayer(uid="p2", name="P2")
        game = _make_game(p1, p2)
        game.start()

        view = p1.decision_views[-1]
        for name in ("deck", "_deck", "table", "_strategies", "event_bus", "_events"):
            self.assertFalse(hasattr(view, name), name)
        for obj in _all_objects(view):
            self.assertNotIsInstance(obj, (Game, Deck, Player))

    def test_view_is_read_only(self):
        p1 = RecordingPlayer(uid="p1", name="P1")
        p2 = RecordingPlayer(uid="p2", name="P2")
        game = _make_game(p1, p2)
        game.start()

        view = p1.decision_views[-1]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            view.state = GameState()
        with self.assertRaises(Exception):
            view.state.pot = 1_000_000

    def test_mutating_view_does_not_affect_game(self):
        game_ref = {}

        class MeddlingPlayer(RecordingPlayer):
            def decide_action(self, *, game, valid_actions, **kwargs):
                real = game_ref["game"]
                before = real.get_player_snapshot(self.uid).state.holding.cards
                before = [c.code() for c in before]
                game.holding.cards.clear()
                game.rules.stakes.big_blind = 999
                game.history[-1].payload["meddled"] = True
                after = real.get_player_snapshot(self.uid).state.holding.cards
                self.after_check = (before, [c.code() for c in after])
                return super().decide_action(
                    game=game, valid_actions=valid_actions, **kwargs
                )

        p1 = MeddlingPlayer(uid="p1", name="P1")
        p2 = RecordingPlayer(uid="p2", name="P2")
        game = _make_game(p1, p2)
        game_ref["game"] = game
        game.start()

        before, after = p1.after_check
        self.assertEqual(before, after)
        self.assertEqual(game.rules.stakes.big_blind, 2)
        self.assertFalse(any("meddled" in e.payload for e in game.history))
        for event in game.history:
            if event.type == GameEventType.PLAYER_CARDS_REVEALED:
                for code in event.payload["holding"]:
                    self.assertIsInstance(code, str)

    def test_returned_action_cannot_be_altered_afterwards(self):
        class TamperingPlayer(RecordingPlayer):
            def decide_action(self, **kwargs):
                self.last_action = super().decide_action(**kwargs)
                return self.last_action

        p1 = TamperingPlayer(uid="p1", name="P1")
        p2 = RecordingPlayer(uid="p2", name="P2")
        game = _make_game(p1, p2)
        game.start()

        p1.last_action.amount = 123_456
        p1.last_action.payload["fake"] = True
        for event in game.history:
            if event.action is not None:
                self.assertNotEqual(event.action.amount, 123_456)
                self.assertNotIn("fake", event.action.payload)
                self.assertIsNotNone(event.action.decision_time_seconds)

    def test_hook_receives_matching_event_when_listener_emits(self):
        p1 = RecordingPlayer(uid="p1", name="P1")
        p2 = RecordingPlayer(uid="p2", name="P2")
        game = _make_game(p1, p2)

        def nested_emit(event, g):
            g._emit(g._create_event(GameEventType.HAND_ENDED))

        game.subscribe(GameEventType.HAND_STARTED, nested_emit)
        game.start()

        hand_started = [
            e for e, _ in p1.event_views if e.type == GameEventType.HAND_STARTED
        ]
        self.assertTrue(hand_started)
        original = {e.uid for e in game.history}
        for event, _ in p1.event_views:
            self.assertIn(event.uid, original)
        self.assertEqual(len({e.uid for e, _ in p1.event_views}), len(p1.event_views))

    def test_game_state_changed_payload_redacted_for_players_only(self):
        external = []
        p1 = RecordingPlayer(uid="p1", name="P1", fold=True)
        p2 = RecordingPlayer(uid="p2", name="P2", fold=True)
        game = _make_game(p1, p2)
        game.subscribe(
            GameEventType.GAME_STATE_CHANGED, lambda e, g: external.append(e)
        )
        game.start()

        # Nobody reaches showdown, so no holding is ever revealed
        self.assertFalse(
            any(e.type == GameEventType.PLAYER_CARDS_REVEALED for e in game.history)
        )
        # External listeners see the full state ...
        self.assertTrue(
            any(_opponent_holdings_in_dump(e.payload["after"], "p1") for e in external)
        )
        # ... players only see their own holding
        for player in (p1, p2):
            state_events = [
                e
                for e, _ in player.event_views
                if e.type == GameEventType.GAME_STATE_CHANGED
            ]
            self.assertTrue(state_events)
            own_seen = False
            for event in state_events:
                for key in ("before", "after"):
                    dump = event.payload[key]
                    self.assertEqual(_opponent_holdings_in_dump(dump, player.uid), [])
                    own_seen |= any(
                        p["uid"] == player.uid and p["state"]["holding"]
                        for p in dump["players"]
                    )
            self.assertTrue(own_seen)
            # State changes are not part of the history held by players
            self.assertFalse(
                any(
                    e.type == GameEventType.GAME_STATE_CHANGED
                    for e in player.game.history
                )
            )

    def test_history_matches_game_history(self):
        p1 = RecordingPlayer(uid="p1", name="P1")
        p2 = RecordingPlayer(uid="p2", name="P2")
        game = _make_game(p1, p2)
        game.subscribe(GameEventType.GAME_STATE_CHANGED, lambda e, g: None)
        game.start()

        view = game.get_player_view(p1)
        expected = [
            e.uid for e in game.history if e.type != GameEventType.GAME_STATE_CHANGED
        ]
        self.assertTrue(len(expected) < len(game.history))
        self.assertEqual([e.uid for e in view.history], expected)
        # Earlier views keep the length they had when they were created
        first_view = p1.event_views[0][1]
        self.assertEqual(len(first_view.history), 1)

    def test_player_game_and_state_properties(self):
        p1 = RecordingPlayer(uid="p1", name="P1")
        p2 = RecordingPlayer(uid="p2", name="P2")
        self.assertIsNone(p1.game)
        self.assertIsNone(p1.state)

        game = _make_game(p1, p2)
        game.start()

        self.assertIsInstance(p1.game, PlayerView)
        self.assertNotIsInstance(p1.game, Game)
        self.assertEqual(p1.state, p1.game.me.state)
        self.assertEqual(p1.state.stack, game.get_player_snapshot(p1).state.stack)

        game.remove_player(p1)
        self.assertIsNone(p1.game)
        self.assertIsNone(p1.state)

    def test_duck_typed_players(self):
        """Players that do not subclass Player also only ever receive views."""
        received = []

        class SilentPlayer:
            def __init__(self, uid, name):
                self.uid, self.name = uid, name

            def decide_action(self, *, game, valid_actions, **_):
                received.append(game)
                action_type = (
                    ActionType.CHECK
                    if ActionType.CHECK in valid_actions
                    else ActionType.CALL
                )
                return PlayerAction(player_uid=self.uid, action_type=action_type)

        class SpecificHookOnly(SilentPlayer):
            def on_hand_started(self, event, game):
                received.append(game)

        game = _make_game(SilentPlayer("p1", "P1"), SpecificHookOnly("p2", "P2"))
        game.start()

        self.assertTrue(received)
        for view in received:
            self.assertIsInstance(view, PlayerView)

    def test_get_player_view_unknown_player(self):
        game = _make_game(RecordingPlayer(uid="p1", name="P1"))
        with self.assertRaises(ValueError):
            game.get_player_view("nobody")


class TestRedaction(unittest.TestCase):
    def setUp(self):
        self.h1 = Holding(
            cards=[
                Card(suit=Suit.SPADES, rank=Rank.ACE),
                Card(suit=Suit.HEARTS, rank=Rank.ACE),
            ]
        )
        self.h2 = Holding(
            cards=[
                Card(suit=Suit.CLUBS, rank=Rank.TWO),
                Card(suit=Suit.DIAMONDS, rank=Rank.SEVEN),
            ]
        )
        self.state = GameState(
            players=[
                PlayerSnapshot(
                    uid="p1", name="P1", state=PlayerState(stack=10, holding=self.h1)
                ),
                PlayerSnapshot(
                    uid="p2", name="P2", state=PlayerState(stack=20, holding=self.h2)
                ),
                PlayerSnapshot(uid="p3", name="P3", state=PlayerState(stack=30)),
            ],
            community_cards=(Card(suit=Suit.SPADES, rank=Rank.KING),),
        )

    def test_redact_state_hides_others(self):
        redacted = redact_state(self.state, "p1")
        self.assertEqual(redacted.players[0].state.holding, self.h1)
        self.assertIsNone(redacted.players[1].state.holding)
        self.assertIsNone(redacted.players[2].state.holding)
        self.assertEqual(redacted.players[1].state.stack, 20)
        # The original is untouched
        self.assertEqual(self.state.players[1].state.holding, self.h2)

    def test_redact_state_keeps_revealed(self):
        redacted = redact_state(self.state, "p1", frozenset({"p2"}))
        self.assertEqual(redacted.players[1].state.holding, self.h2)

    def test_redact_state_returns_independent_copy(self):
        redacted = redact_state(self.state, "p1")
        own = redacted.players[0].state.holding
        self.assertIsNot(own, self.h1)
        self.assertIsNot(own.cards, self.h1.cards)
        own.cards.clear()
        self.assertEqual(len(self.h1.cards), 2)
        # Cards themselves are immutable and can be shared safely
        with self.assertRaises(Exception):
            redacted.community_cards[0].rank = Rank.TWO

    def test_redact_event_game_state_changed(self):
        dump = self.state.model_dump(mode="json")
        event = GameEvent(
            type=GameEventType.GAME_STATE_CHANGED,
            hand_number=1,
            payload={"before": dump, "after": dump},
        )
        redacted = redact_event(event, "p1")
        for key in ("before", "after"):
            players = redacted.payload[key]["players"]
            self.assertIsNotNone(players[0]["state"]["holding"])
            self.assertIsNone(players[1]["state"]["holding"])
        # The original payload is untouched
        self.assertIsNotNone(event.payload["after"]["players"][1]["state"]["holding"])

        revealed = redact_event(event, "p1", frozenset({"p2"}))
        self.assertIsNotNone(
            revealed.payload["after"]["players"][1]["state"]["holding"]
        )

    def test_redact_event_tolerates_missing_state_dump(self):
        event = GameEvent(
            type=GameEventType.GAME_STATE_CHANGED,
            hand_number=1,
            payload={"before": None, "after": {"players": []}},
        )
        self.assertEqual(redact_event(event, "p1"), event)

    def test_redact_event_unpicklable_payload(self):
        callback = lambda: None  # noqa: E731
        event = GameEvent(
            type=GameEventType.HAND_ENDED,
            hand_number=1,
            payload={"callback": callback, "items": [1, 2]},
        )
        redacted = redact_event(event, "p1")
        self.assertIs(redacted.payload["callback"], callback)
        self.assertIsNot(redacted.payload["items"], event.payload["items"])

    def test_redact_event_other_types_are_copied(self):
        event = GameEvent(
            type=GameEventType.PLAYER_CARDS_REVEALED,
            hand_number=1,
            player_uid="p2",
            payload={"holding": ["2C", "7D"]},
        )
        redacted = redact_event(event, "p1")
        self.assertEqual(redacted, event)
        self.assertIsNot(redacted.payload, event.payload)

    def test_from_state(self):
        rules = Game(small_blind=1, big_blind=2).rules
        event = GameEvent(
            type=GameEventType.GAME_STATE_CHANGED,
            hand_number=1,
            payload={"after": self.state.model_dump(mode="json")},
        )
        view = PlayerView.from_state(
            player_uid="p2", state=self.state, rules=rules, history=[event]
        )
        self.assertEqual(view.holding, self.h2)
        self.assertIsNone(view.get_player_snapshot("p1").state.holding)
        self.assertIsNone(view.get_player_snapshot("unknown"))
        self.assertIsNot(view.rules, rules)
        self.assertIsNone(
            view.history[0].payload["after"]["players"][0]["state"]["holding"]
        )

    def test_view_of_player_not_in_game(self):
        view = PlayerView.from_state(
            player_uid="ghost",
            state=self.state,
            rules=Game(small_blind=1, big_blind=2).rules,
        )
        self.assertIsNone(view.me)
        self.assertIsNone(view.holding)


class TestEventHistoryView(unittest.TestCase):
    def setUp(self):
        self.events = [
            GameEvent(type=GameEventType.HAND_STARTED, hand_number=i) for i in range(3)
        ]

    def test_fixed_length_window(self):
        history = EventHistoryView(self.events)
        self.events.append(GameEvent(type=GameEventType.HAND_ENDED, hand_number=3))
        self.assertEqual(len(history), 3)
        self.assertEqual(len(list(history)), 3)
        self.assertEqual(history[-1].hand_number, 2)
        self.assertEqual([e.hand_number for e in history[1:]], [1, 2])
        self.assertIsInstance(history[:], tuple)
        with self.assertRaises(IndexError):
            history[3]
        with self.assertRaises(IndexError):
            history[-4]
        self.assertIn("len=3", repr(history))

    def test_explicit_length(self):
        history = EventHistoryView(self.events, length=1)
        self.assertEqual(len(history), 1)


if __name__ == "__main__":
    unittest.main()
