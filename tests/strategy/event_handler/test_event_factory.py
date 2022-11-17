from strategy.event_handler.event_factory import process_event
from strategy.event_handler.produce import produce

def test_event_factory():
    """Test event factory."""
    fnc = process_event("produce")
    assert fnc == produce
