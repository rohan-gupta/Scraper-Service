import os
import ujson
import boto3
from boto3.dynamodb.conditions import Key
import strategy.condition as condition
import strategy.strategy as strategy_mod
import strategy.recommendation as recommendation
from strategy.signals import check_signals
from scrapehelper.helper import get_decompressed_data_gzip

def produce(gather_event):
    """Create next gather event for scraper."""
    hash_id = gather_event["scraped_data_hash"]
    strategies = gather_event["strategy"]
    data = read_from_dynamodb(hash_id)

    gather_event, stop_scrape = apply_strategy(strategies, gather_event, data)

    if not stop_scrape:
        gather_event = recommendation.apply_ip_recommendation(gather_event)
        send_message_to_sns(gather_event)
    return "Done"

def read_from_dynamodb(hash_id):
    """Read from dynamodb on raw data scraped."""
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.getenv("DATA_TABLE"))
    scraped_data = ""
    for reference in hash_id.split(","):
        queried = table.query(
            KeyConditionExpression=Key("hash_id").eq(reference)
        )
        if queried["Count"] <= 0:
            return None
        if isinstance(queried["Items"][0]["data"], str):
            scraped_data += queried["Items"][0]["data"]
        else:
            scraped_data = queried["Items"][0]["data"]
    try:
        scraped_data = ujson.loads(get_decompressed_data_gzip(scraped_data))
    except Exception as e:
        print(e)
    return scraped_data

def send_message_to_sns(gather_event):
    """Send gather event to sns."""
    session = boto3.session.Session()
    sns = session.client("sns")
    gather_event["sns_event_type"] = "gather"
    message = ujson.dumps(gather_event)

    sns_name = os.getenv("SNS_GATHER")

    response = sns.publish(
        TopicArn=sns_name,
        Message=message,
        MessageAttributes={
            "lambda_name": {
                "DataType": "String",
                "StringValue": gather_event["current_lambda"]
            },
            "scraper_type": {
                "DataType": "String",
                "StringValue": gather_event["scraper_type"]
            }
        }
    )
    return response

def apply_strategy(strategies, gather_event, data):
    """Check for conditions and apply strategies accordingly."""
    stop_scrape = True
    if check_signals(gather_event["service_name"], gather_event["country_code"]):
        for strategy in strategies:
            cond = strategy["condition"]
            check_for_condition = getattr(condition, cond["method"])
            if check_for_condition(cond, data, gather_event=gather_event):
                strategy_method = getattr(strategy_mod, strategy["method"])
                stop_scrape, gather_event = strategy_method(gather_event, strategy, data)
                if stop_scrape:
                    break
                stop_scrape = False
    return gather_event, stop_scrape
