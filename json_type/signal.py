import os
import ujson
import time
import boto3

def send_signal(signal_name, ip, source=None, message_attributes=None):
    """Send signals on what the scraper is doing."""
    session = boto3.session.Session()
    sns = session.client("sns")
    message = {
        "ip_address": ip,
        "scraper_type": "api",
        "timestamp": time.time(),
        "signal_name": signal_name.upper(),
        "lambda_name": os.getenv("CURRENT_LAMBDA")
    }
    if source:
        message.update(
            {
                "service_name": source
            }
        )
    message = ujson.dumps(message)

    sns_name = os.getenv("SNS_SIGNAL")

    response = sns.publish(
        TopicArn=sns_name,
        Message=message,
        MessageAttributes=message_attributes if message_attributes else {}
    )
    return response