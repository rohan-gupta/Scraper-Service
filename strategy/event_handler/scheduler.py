from strategy.event_handler.produce import send_message_to_sns
from strategy.signals import check_signals

def scheduler(gather_event):
    """Send gather event for scraper."""
    if check_signals(gather_event["service_name"], gather_event["country_code"], t=gather_event.get("scheduler_time")):
        send_message_to_sns(gather_event)
    return "Done"
