"""Module for saving scraped data."""
import os
import time
import json
from uuid import uuid4

def publish(data, gather_event):
    """Publish data for other services to consume."""
    options = publish_options(data)
    produce_event = create_produce_event(data, gather_event, options)
    sns_message = construct_sns_message(gather_event, produce_event)
    ###TODO: CREATE SNS FUNCTION.
    # send_to_sns(sns_message, sns_name)

def publish_options(data):
    """Check what publishing method should
    be used depending on data."""
    ###only dynamodb for now, we can have other methods for varying data size
    return "dynamodb"

def create_produce_event(data, gather_event, options):
    """Create produce event based on data and publish options."""
    service_name = gather_event["service_name"]
    country_code = gather_event["country_code"]
    event_message = {
        "options": options
    }
    if options == "dynamodb":
        partition_key = f"{service_name}|{country_code}"
        sort_key = str(uuid4())
        ttl = time.time() + 3600
        event_message.update(
            {
                "partition_key": partition_key,
                "sort_key": sort_key
            }
        )
        ####TODO CREATE SAVING FUNCTION.
        # save_to_dynamodb(partition_key, sort_key, data, ttl)
    return event_message

def construct_sns_message(gather_event, produce_event):
    """Construct sns message to be published."""
    sns_message = {
        "gather_event": gather_event,
        "produce_event": produce_event
    }
    return json.dumps(sns_message)
