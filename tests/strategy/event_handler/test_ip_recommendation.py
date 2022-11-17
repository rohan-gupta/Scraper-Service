import time
import pytest
import boto3
from boto3.dynamodb.conditions import Key
from moto import mock_dynamodb2
import strategy.event_handler.ip_recommendation as ip_recommendation

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
    return 123

def test_save_recommendation_to_dynamodb(_mock_env_dynamodb, monkeypatch):
    """Test save to dynamodb function."""
    message = {
        "service_name": "ubereats",
        "scraper_type": "api",
        "lambda_name": "scraper1",
        "sns_event_type": "ip_recommendation"
    }
    monkeypatch.setattr(time, "time", mock_time)
    ip_recommendation.save_ip_recommendation(
        message
    )
    dynamodb = boto3.resource("dynamodb")
    dynamodb = dynamodb.Table("test_signal_table")
    item = dynamodb.query(
        KeyConditionExpression=Key("source").eq("ubereats") & Key("signalType").eq("ip_recommendation")
    )

    assert item["Items"][0] == {
        'source': 'ubereats',
        'signalType': 'ip_recommendation',
        'lambda_name': 'scraper1',
        'scraper_type': 'api',
        "expired": 0
    }
