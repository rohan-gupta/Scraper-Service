"""Handler module for initiator."""
try:
    import unzip_requirements
except ImportError:
    pass
import os
import time
from uuid import uuid4
import ujson
import boto3
import requests
from initiator.initiator import initiator_factory

def main(event, _context):
    """Handler for initiator."""
    headers = event["headers"]
    message = ujson.loads(event["body"])

    if check_authorizations(headers):
        if message["sns_event_type"] == "initiation":
            create_gather_event = initiator_factory(message["initiator_type"])
            gather_event = create_gather_event(message)
            send_gather_event(gather_event)

            response = {
                "statusCode": 200,
                "headers": {
                    "content-type": "application/json"
                },
                "body": "scraping has been initiated",
                "isBase64Encoded": False,
            }
        elif message["sns_event_type"] == "stop":
            send_stop_signal(message)
            response = {
                "statusCode": 200,
                "headers": {
                    "content-type": "application/json"
                },
                "body": "stop signal has been sent",
                "isBase64Encoded": False,
            }
        return response
    return "Message not processed"

def check_authorizations(headers):
    """Check that authorizations and api key is in header."""
    if headers.get("api-key") != os.getenv("API_KEY"):
        return False
    return True

def send_gather_event(event):
    """Send gather event to initiate scraper."""
    session = boto3.session.Session()
    sns = session.client("sns")
    event["sns_event_type"] = "gather"
    event["process_id"] = str(uuid4())
    event["initiation_metadata"] = {
        "variables": event.get("variables"),
        "timestamp": int(time.time())
    }
    message = ujson.dumps(event)

    sns_name = os.getenv("SNS_GATHER")

    message_attributes = {
        "lambda_name": {
            "DataType": "String",
            "StringValue": event["current_lambda"]
        },
        "scraper_type": {
            "DataType": "String",
            "StringValue": event["scraper_type"]
        }
    }

    response = sns.publish(
        TopicArn=sns_name,
        Message=message,
        MessageAttributes=message_attributes
    )
    return response

def send_stop_signal(message):
    """Send stop signal to strategy service."""
    session = boto3.session.Session()
    sns = session.client("sns")
    message["sns_event_type"] = "stop"
    message = ujson.dumps(message)

    sns_name = os.getenv("SNS_SIGNAL_INCOMING")

    response = sns.publish(
        TopicArn=sns_name,
        Message=message
    )
    return response
