import pytest

from levi.streaming.bus import EventBus
from tests.test_streaming_events import event
from tests.streaming_helpers import run


def test_bus_delivers_to_subscribed_user():
    async def scenario():
        bus = EventBus(); queue = bus.subscribe("u1")
        assert await bus.publish(event()) == 1
        assert (await queue.get()).user_id == "u1"
    run(scenario())


def test_bus_does_not_deliver_to_another_user():
    async def scenario():
        bus = EventBus(); other = bus.subscribe("u2")
        await bus.publish(event())
        assert other.empty()
    run(scenario())


def test_bus_supports_multiple_same_user_subscribers():
    async def scenario():
        bus = EventBus(); first = bus.subscribe("u1"); second = bus.subscribe("u1")
        assert await bus.publish(event()) == 2
        assert not first.empty() and not second.empty()
    run(scenario())


def test_bus_drops_when_no_subscriber_without_error():
    assert run(EventBus().publish(event())) == 0


def test_bus_unsubscribe_stops_delivery():
    async def scenario():
        bus = EventBus(); queue = bus.subscribe("u1"); bus.unsubscribe("u1", queue)
        assert await bus.publish(event()) == 0 and queue.empty()
    run(scenario())


def test_bus_rejects_blank_subscription_owner():
    with pytest.raises(ValueError, match="user_id"):
        EventBus().subscribe(" ")
