"""Handler module for json scraper."""
try:
    import unzip_requirements
except ImportError:
    pass
import os
import ujson
import requests
from json_type.scrape import start_scrape
from json_type.signal import send_signal

##will run only on coldstart initiation
if os.getenv("COLD_START") == "true":
    ip = requests.get('http://checkip.amazonaws.com').text.rstrip()
    send_signal("init", ip)

def main(event, _context):
    """Handler for json scraper."""
    os.environ["COLD_START"] = "false"
    sqs_message = event["Records"][0]["body"]
    if validate_message(sqs_message):
        start_scrape(ujson.loads(sqs_message))
        return "Scraping has finished"
    return "Message not processed"

def validate_message(message):
    """Validate that the message is something to be processed."""
    try:
        message = ujson.loads(message)
        if message["sns_event_type"] != "gather":
            return False
        if message["scraper_type"] != "api":
            return False
        if all(key in message.keys() for key in ("scope", "variables",
                                                 "service_name", "country_code", "strategy")):
            if all(key in message["scope"].keys() for key in ("url", "method")):
                return True
        return False

    except Exception as e:
        print(e)
        return False
