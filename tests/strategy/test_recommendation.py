"""Test all the different strategies available."""
import time
import pytest
import ujson
import boto3
from moto import mock_dynamodb2
import strategy.recommendation as recommendation


@pytest.fixture
def _mock_env_dynamodb(monkeypatch):
    """Mock environment for dynamodb unit test functions."""
    monkeypatch.setenv("SIGNAL_TABLE", "test_signal_table")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-southeast-1")
    mock = mock_dynamodb2()
    mock.start()
    dynamodb = boto3.resource("dynamodb")
    dynamodb.create_table(
        AttributeDefinitions=[
            {
                "AttributeName": "source",
                "AttributeType": "S"
            },
            {
                "AttributeName": "signalType",
                "AttributeType": "S"
            }
        ],
        TableName="test_signal_table",
        KeySchema=[
            {
                "AttributeName": "source",
                "KeyType": "HASH"
            },
            {
                "AttributeName": "signalType",
                "KeyType": "RANGE"
            }
        ],
        BillingMode="PAY_PER_REQUEST"
    )
    yield dynamodb
    mock.stop()

def mock_time():
    """Mock time function."""
    return 130

def test_ip_recommendation(monkeypatch, _mock_env_dynamodb):
    """Test ip recommendation strategy."""
    monkeypatch.setenv("AVAILABLE_LAMBDAS", "scraper1,scraper2,scraper3,scraper10")
    with open("tests/common_test_data/gather_event.json", "r") as test_f:
        gather_event = ujson.load(test_f)[0]
    gather_event['service_name'] = "ubereats"

    gather_event = recommendation.apply_ip_recommendation(gather_event)
    assert gather_event["current_lambda"] == "scraper2"

    dynamodb = boto3.resource("dynamodb")
    dynamodb = dynamodb.Table("test_signal_table")
    monkeypatch.setattr(time, "time", mock_time)
    dynamodb.put_item(
        Item={
                "source": "ubereats",
                "signalType": "ip_recommendation",
                "lambda_name": "scraper10",
                "expired": 0
        }
    )
    gather_event = recommendation.apply_ip_recommendation(gather_event)
    assert gather_event["current_lambda"] == "scraper10"

    dynamodb.put_item(
        Item={
                "source": "ubereats",
                "signalType": "ip_recommendation",
                "lambda_name": "scraper10",
                "expired": 1
        }
    )
    gather_event = recommendation.apply_ip_recommendation(gather_event)
    assert gather_event["current_lambda"] == "scraper1"
