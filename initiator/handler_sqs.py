"""Handler module for initiator."""
try:
    import unzip_requirements
except ImportError:
    pass
import ujson
from initiator.gather.gather import Gather

def main(event, _context):
    """Handler for produce event."""
    message = event["Records"][0]["body"]
    message = ujson.loads(message)
    if validate_message(message):
        initiator_message = message["initiator"].pop(0)
        Gather(message, initiator_message).process()
        return "Scraping has been initiated"
    return "Message not processed"

def validate_message(message):
    """Validate that the message is something to be processed."""
    if message.get("sns_event_type") != "produce":
        return False
    if message.get("initiator"):
        return True
    return False
