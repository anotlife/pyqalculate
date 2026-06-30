"""Tests for the EventBus publish-subscribe system."""

from __future__ import annotations

from pyqalculate_gui.event_bus import EventBus


class TestEventBus:
    def test_subscribe_and_emit(self) -> None:
        bus = EventBus()
        received: list[str] = []
        bus.subscribe("test_event", lambda msg: received.append(msg))
        bus.emit("test_event", "hello")
        assert received == ["hello"]

    def test_multiple_subscribers(self) -> None:
        bus = EventBus()
        results: list[int] = []
        bus.subscribe("ev", lambda: results.append(1))
        bus.subscribe("ev", lambda: results.append(2))
        bus.emit("ev")
        assert results == [1, 2]

    def test_unsubscribe(self) -> None:
        bus = EventBus()
        received: list[str] = []
        callback = lambda msg: received.append(msg)
        bus.subscribe("ev", callback)
        bus.unsubscribe("ev", callback)
        bus.emit("ev", "gone")
        assert received == []

    def test_emit_no_subscribers(self) -> None:
        bus = EventBus()
        # Should not raise
        bus.emit("nonexistent", 1, 2, key="val")

    def test_deduplication(self) -> None:
        bus = EventBus()
        call_count = 0

        def handler() -> None:
            nonlocal call_count
            call_count += 1

        bus.subscribe("ev", handler)
        bus.subscribe("ev", handler)
        bus.emit("ev")
        assert call_count == 1
