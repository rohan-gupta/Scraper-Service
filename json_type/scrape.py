###Module to construct request object and send scraping requests
import re
import os
import copy
import time
from base64 import b64encode
import requests
from decimal import Decimal
from uuid import uuid4
import boto3
import ujson
from json_type.signal import send_signal
from scrapehelper.useragents import get_web_browser_user_agent
from scrapehelper.helper import get_compressed_data_gzip

def start_scrape(gather_event):
    """Start scraping function."""
    request_details = copy.deepcopy(gather_event["scope"])
    variables = gather_event.get("variables")
    source = gather_event["service_name"]
    print(ujson.dumps({
        **variables,
        "source": source,
        "country_code": gather_event["country_code"]
        }
    ))
    request_object = construct_request_object(request_details, variables)
    ip = "mock_ip"
    log_scraper(ip, source, gather_event["country_code"])
    send_signal("start", ip, source=source)
    scraped_data, cookies, status_code = send_scraping_request(request_object)
    send_signal("end", ip, source=source)

    produce_event = create_produce_event(gather_event, scraped_data, cookies, status_code)
    send_to_sns(produce_event)
    return "Done"

def construct_request_object(request_details, variables):
    """Replace variables in request object if needed."""
    request_object = {}
    for key, values in request_details.items():
        values = replace_variables(values, variables)
        request_object[key] = values
    if "headers" not in request_object:
        request_object["headers"] = {}
    if "User-Agent" not in request_object["headers"] and \
        "user-agent" not in request_object["headers"]:
        request_object["headers"]["User-Agent"] = get_web_browser_user_agent(
            bucket=os.getenv("STAGE")
        )["userAgent"]

    return request_object

def replace_variables(values, variables):
    """Check if there's variables within the values and replace if needed."""
    ###replace variables enclosed in {[]} with actual values
    pattern = r"\{\[(.*?)\]\}"
    if isinstance(values, dict):
        for k, v in values.items():
            values[k] = replace_variables(v, variables)
    elif isinstance(values, list):
        for i in range(len(values)):
            values[i] = replace_variables(values[i], variables)
    else:
        matches = re.findall(pattern, str(values))
        if matches:
            for match in matches:
                if f'{{[{match}]}}' == values:
                    values = variables[match]
                else:
                    values = values.replace(f"{{[{match}]}}", str(variables[match]))
    return values

def send_scraping_request(request_object):
    """Send request object and obtain data."""
    response = requests.request(**request_object)
    cookies = response.cookies.get_dict()
    try:
        data = response.json()
    except Exception:
        data = {"error_response": response.text}
    return data, cookies, response.status_code

def create_produce_event(gather_event, scraped_data, cookies, status_code):
    """Create produce event."""
    produce_event = gather_event
    hash_id = save_data(scraped_data, cookies)
    produce_event["sns_event_type"] = "produce"
    produce_event["scraped_data_hash"] = hash_id
    produce_event["response_status_code"] = status_code
    return produce_event

def save_data(scraped_data, cookies):
    """Save data to temp db with generated hash id."""
    reference_hash = ""
    dynamodb = boto3.resource("dynamodb")
    compressed_scraped_data = b64encode(get_compressed_data_gzip(ujson.dumps(scraped_data))).decode("ascii")
    compressed_cookies = b64encode(get_compressed_data_gzip(ujson.dumps(cookies))).decode("ascii")
    compressed_partitions = get_partition_from_size(compressed_scraped_data)
    table = dynamodb.Table(os.getenv("DATA_TABLE"))
    for partition in compressed_partitions:
        hash_id = str(uuid4())
        to_save = {
            "hash_id": hash_id,
            "data": partition,
            "cookies": compressed_cookies,
            "TimeToExist": int(time.time()) + 3600
        }
        to_save = float_to_decimal(to_save)

        table.put_item(Item=to_save)
        reference_hash += f"{hash_id},"
    reference_hash = reference_hash[:-1]
    print("hash_id: ", reference_hash)
    return reference_hash

def get_partition_from_size(data):
    """Get partition based on data size."""
    n = int(len(data)/370000)
    if len(data)%370000:
        n = n+1
    partitions = [data[i*370000:(i+1)*370000] for i in range(n)]
    return partitions

def send_to_sns(produce_event):
    """Send produce event to sns."""
    session = boto3.session.Session()
    sns = session.client("sns")
    message = ujson.dumps(produce_event)

    sns_name = os.getenv("SNS_PRODUCE")
    message_attributes = {
        "initiator": {
            "DataType": "String",
            "StringValue": "1" if produce_event.get("initiator") else "0"
        }
    }

    response = sns.publish(
        TopicArn=sns_name,
        Message=message,
        MessageAttributes=message_attributes if message_attributes else {}
    )
    return response

def log_scraper(ip, source, country_code):
    """Temporary log for datadog metrics."""
    print(
        ujson.dumps({
            "lambda": os.getenv("CURRENT_LAMBDA"),
            "ip": ip,
            "service_name": source,
            "country_code": country_code
        })
    )

def float_to_decimal(data):
    """Returns values converted to decimal type and empty strings values are removed."""
    if isinstance(data, dict):
        return dict((k, float_to_decimal(v)) for k, v in data.items())
    if isinstance(data, list):
        return list(float_to_decimal(item) for item in data)
    if isinstance(data, float):
        return Decimal(str(data))
    return data