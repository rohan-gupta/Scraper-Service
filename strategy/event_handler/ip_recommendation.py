import os
import boto3

def ip_recommendation(message):
    """Save ip recommendation data to DB."""
    save_ip_recommendation(message)

def save_ip_recommendation(message):
    """Save ip recommendation signal when it's received."""
    dynamodb = boto3.resource("dynamodb")
    data = {
        "source": message["service_name"],
        "signalType": "ip_recommendation",
        "lambda_name": message["lambda_name"],
        "scraper_type": message["scraper_type"],
        "expired": 0
    }
    table = dynamodb.Table(os.getenv("SIGNAL_TABLE"))
    response = table.put_item(Item=data)
    return response