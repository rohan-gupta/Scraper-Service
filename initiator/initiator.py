"""Module for initiator."""
import os
import boto3
import yaml

def config(message):
    """Create gather event based on config."""
    path = message["path"]
    s3 = boto3.resource("s3")
    try:
        s3_object = s3.Object(
            f"{os.getenv('VCI_BUCKET')}",
            path
        )
        config_file = s3_object.get()["Body"].read()
        scraper_config = yaml.safe_load(config_file)

    except Exception as ex:
        message = f"Error: {ex}"
        print(message)
        scraper_config = None
    return scraper_config

def message(message):
    """Create gather event based on message."""
    gather_event = message["message"]
    return gather_event

def initiator_factory(method_type):
    """Function to retrieve which method to use."""
    methods = {
        "config": config,
        "message": message
    }
    return methods[method_type]