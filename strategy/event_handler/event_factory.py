"""Module to process event messages."""
from strategy.event_handler.produce import produce
from strategy.event_handler.stop import stop
from strategy.event_handler.ip_recommendation import ip_recommendation
from strategy.event_handler.scheduler import scheduler

def process_event(event_name):
    """Handler for event processing."""
    event_factory = {
        "produce": produce,
        "stop": stop,
        "ip_recommendation": ip_recommendation,
        "scheduler": scheduler
    }
    return event_factory[event_name]
