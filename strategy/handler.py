"""Handler for continuous strategy lambda."""
try:
    import unzip_requirements
except ImportError:
    pass
import ujson
from strategy.event_handler.event_factory import process_event

def main(event, _context):
    """Main handler for continuous strategy lambda."""
    message = event["Records"][0]["Sns"]["Message"]
    message = ujson.loads(message)
    event_type = message["sns_event_type"]
    event_processor = process_event(event_type)
    event_processor(message)
    return "Done"
