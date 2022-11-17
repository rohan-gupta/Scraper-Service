"""Module to handle incoming signals."""
import os
import time
import boto3
from boto3.dynamodb.conditions import Key

def check_signals(service_name, country_code, t=None):
    """Check signals whether scraping is a go."""
    if not t:
        t = int(time.time())
    else:
        t = int(t)
    return check_stop_signal_db(service_name, country_code, t)

def check_stop_signal_db(service_name, country_code, t):
    """Check if stop signal is present."""
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.getenv("SIGNAL_TABLE"))
    response = table.query(
        KeyConditionExpression=Key("source").eq(f"{service_name}|{country_code}") & Key("signalType").eq("stop"),
        ScanIndexForward=False
    )
    if response["Count"] <= 0:
        return True
    else:
        if response["Items"][0]["expiry"] <= t:
            return True
    print("stop signal not present")
    return False

def save_stop_signal_db(message):
    """Save stop signal when it's received."""
    dynamodb = boto3.resource("dynamodb")
    data = {
        "source": f'{message["service_name"]}|{message["country_code"]}',
        "signalType": "stop",
        "expiry": int(time.time()) + 300
    }
    table = dynamodb.Table(os.getenv("SIGNAL_TABLE"))
    response = table.put_item(Item=data)
    return response