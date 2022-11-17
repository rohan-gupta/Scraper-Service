from abc import ABC, abstractmethod
import os
import ujson
import boto3
from boto3.dynamodb.conditions import Key

class Recommendation(ABC):
    """Base clase for IP recommendation strategy."""
    def __init__(self, gather_event):
        """Initiate class."""
        self.current_lambda = gather_event["current_lambda"]
        self.source = gather_event["service_name"]

    @abstractmethod
    def get_ip(self):
        """Abstract method to get ip recommendation."""
        pass

    def default_ip_recommendation(self):
        """Default method to get next ip round robin way."""
        lambdas = os.getenv("AVAILABLE_LAMBDAS")
        lambda_list = lambdas.split(",")
        current_index = lambda_list.index(self.current_lambda)
        try:
            next_ip = lambda_list[current_index+1]
        except IndexError:
            next_ip = lambda_list[0]
        return next_ip

class Cheetah(Recommendation):
    """Getting geolocation from s3."""
    def get_ip(self):
        """Implement getting next ip from pathfinder."""
        try:
            next_ip = self.check_recommendation_signals()
            if next_ip:
                print(
                    ujson.dumps(
                        {
                            "service_name": self.source,
                            "ip": next_ip,
                            "type": "recommendation"
                        }
                    )
                )
                return next_ip
            return self.default_ip_recommendation()

        except Exception as e:
            print(e)
            return self.default_ip_recommendation()

    def check_recommendation_signals(self):
        """Check recommendation signals in signal DB."""
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(os.getenv("SIGNAL_TABLE"))
        recommendation = table.query(
            KeyConditionExpression=Key("source").eq(self.source) & Key("signalType").eq("ip_recommendation"),
            ConsistentRead=True
        )
        if recommendation["Count"] <= 0:
            return None
        recommendation = recommendation["Items"][0]
        if recommendation["expired"]:
            return None
        recommendation["expired"] = 1
        table.put_item(Item=recommendation)
        return recommendation["lambda_name"]

def apply_ip_recommendation(gather_event):
    """Function to retrieve which method to use."""
    cheetah = Cheetah(gather_event)
    gather_event["current_lambda"] = cheetah.get_ip()
    return gather_event
