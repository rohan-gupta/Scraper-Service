"""Module related to creating gather events."""
import os
import copy
import time
from uuid import uuid4
import ujson
import boto3
from boto3.dynamodb.conditions import Key
from jsonpath_ng.ext import parse
from initiator.gather.variables import variables_factory
from scrapehelper.helper import get_decompressed_data_gzip

class Gather():
    def __init__(self, gather_event, initiation_message):
        """Init function."""
        self.gather_event = gather_event
        self.initiation_message = initiation_message

        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(os.getenv("DATA_TABLE"))
        scraped_data = ""
        hash_id = gather_event["scraped_data_hash"]
        for reference in hash_id.split(","):
            queried = table.query(
                KeyConditionExpression=Key("hash_id").eq(reference)
            )
            if queried["Count"] <= 0:
                self.data = None
                self.cookies = None
            else:
                if isinstance(queried["Items"][0]["data"], str):
                    scraped_data += queried["Items"][0]["data"]
                else:
                    scraped_data = queried["Items"][0]["data"]
                try:
                    scraped_data = ujson.loads(get_decompressed_data_gzip(scraped_data))
                except Exception as e:
                    print(e)

                cookies = None

                try:
                    cookies = ujson.loads(get_decompressed_data_gzip(queried["Items"][0]["cookies"]))
                except Exception as e:
                    print(e)

                self.data = scraped_data
                self.cookies = cookies

    def post_processing(self):
        """Post processing to send gather event."""
        gather_event = self.gather_event
        initiation_message = self.initiation_message

        gather_event["sns_event_type"] = "gather"

        gather_event["mapper_config"] = initiation_message.get("mapper_config") if initiation_message.get("mapper_config") else []
        if initiation_message.get("scraper_type"):
            gather_event["scraper_type"] = initiation_message["scraper_type"]
        gather_event["scope"] = initiation_message.get("scope")
        gather_event["scraping_type"] = initiation_message.get("scraping_type")
        gather_event["strategy"] = initiation_message.get("strategy") if initiation_message.get("strategy") else []
        gather_event["process_id"] = str(uuid4())
        gather_event["initiation_metadata"] = {
            "variables": gather_event.get("variables"),
            "timestamp": int(time.time())
        }

        message = ujson.dumps(gather_event)

        sns_name = os.getenv("SNS_GATHER")

        message_attributes = {
            "lambda_name": {
                "DataType": "String",
                "StringValue": gather_event["current_lambda"]
            },
            "scraper_type": {
                "DataType": "String",
                "StringValue": gather_event["scraper_type"]
            }
        }
        response = self.client.publish(
            TopicArn=sns_name,
            Message=message,
            MessageAttributes=message_attributes
        )
        return gather_event, response

    def process(self):
        """Process initiation message."""
        initiation_message = self.initiation_message
        json_path = parse(initiation_message["json_path"])
        self.client = boto3.client("sns")
        try:
            data = json_path.find(self.data)
        except Exception as e:
            print(e)
            return "Data not found", "Data not found"
        if not data:
            return "Data not found", "Data not found"

        if initiation_message.get("group_length"):
            length = initiation_message["group_length"]
            data = [[datum.value for datum in data[i:i+length]] for i in range(0, len(data), length)]
        else:
            data = [datum.value for datum in data]

        for datum in data:
            variables = self.create_variables(datum, initiation_message["variables"])
            self.gather_event["variables"].update(variables)
            response, sns_response = self.post_processing()
        return response, sns_response

    def create_variables(self, data, message):
        """Create variables dict based on message."""
        variables = {}
        for k,v in message.items():
            variable = copy.deepcopy(data)
            for method in v:
                get_variable = variables_factory(method["method"])
                variable = get_variable(variable, method, self.cookies)
            variables[k] = variable
        return variables
