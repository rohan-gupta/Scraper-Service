"""Module that contains all the different strategy."""
import os
import time
import boto3
import ujson
from jsonpath_ng.ext import parse
from strategy.geolocation import geolocation_factory

def value_increment(gather_event, strategy, _data):
    """Value increment strategy."""
    value = strategy["value"]
    variables = gather_event["variables"]
    targets = strategy["target"]
    for target in targets:
        variables[target] += value
    gather_event["variables"] = variables
    return False, gather_event

def set_value(gather_event, strategy, _data):
    """Set value strategy."""
    value = strategy["value"]
    variables = gather_event["variables"]
    targets = strategy["target"]
    for target in targets:
        variables[target] = value
    gather_event["variables"] = variables
    return False, gather_event

def geolocation(gather_event, strategy, _data):
    """geolocation strategy."""
    method_type = strategy["type"]
    variables = gather_event["variables"]
    latitude = variables[strategy["target"][0]]
    longitude = variables[strategy["target"][1]]
    Geo = geolocation_factory(method_type)(latitude, longitude, strategy)
    next_lat_lng = Geo.get_lat_lng()
    gather_event["variables"][strategy["target"][0]] = next_lat_lng.split(",")[0]
    gather_event["variables"][strategy["target"][1]] = next_lat_lng.split(",")[1]

    return False, gather_event

def retrieve_data(gather_event, strategy, data):
    """Get variables value from scraped data."""
    jsonpath_expr = strategy["json_path"]
    variables = gather_event["variables"]
    default = strategy["default"]

    targets = strategy["target"]

    jsonpath_expr = parse(jsonpath_expr)
    try:
        extracted_val = jsonpath_expr.find(data)[0].value
        for target in targets:
            variables[target] = extracted_val
    except Exception:
        for target in targets:
            variables[target] = default
    gather_event["variables"] = variables

    return False, gather_event

def schedule_event(gather_event, strategy, data):
    """Schedule gather event to be sent later."""
    session = boto3.session.Session()
    sns = session.client("sns")
    gather_event["sns_event_type"] = "gather"
    scheduled_time = int(time.time())+ int(strategy["delay"])

    message = ujson.dumps({
        "message": gather_event,
        "target": "strategy",
        "time": scheduled_time
    })

    sns_name = os.getenv("SNS_SCHEDULER")

    response = sns.publish(
        TopicArn=sns_name,
        Message=message
    )
    return True, response