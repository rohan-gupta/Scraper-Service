import pytest
import boto3
import ujson
from moto import mock_dynamodb2, mock_sns
import strategy.event_handler.produce as produce
import strategy.condition as condition
import strategy.strategy as strategy_mod

@pytest.fixture
def _mock_env_dynamodb(monkeypatch):
    """Mock environment for dynamodb unit test functions."""
    monkeypatch.setenv("DATA_TABLE", "test_data_table")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-southeast-1")
    mock = mock_dynamodb2()
    mock.start()
    dynamodb = boto3.resource("dynamodb")
    dynamodb.create_table(
        AttributeDefinitions=[
            {
                "AttributeName": "hash_id",
                "AttributeType": "S"
            }
        ],
        TableName="test_data_table",
        KeySchema=[
            {
                "AttributeName": "hash_id",
                "KeyType": "HASH"
            }
        ],
        BillingMode="PAY_PER_REQUEST"
    )
    dynamodb = dynamodb.Table("test_data_table")
    dynamodb.put_item(
        Item={
                "hash_id": "123",
                "data": "mock_data"
        }
    )
    yield dynamodb
    mock.stop()

@pytest.fixture
def _mock_env_sns(monkeypatch):
    """Mock environment for sns unit test functions."""
    mock = mock_sns()
    mock.start()
    monkeypatch.setenv("SNS_GATHER", "arn:aws:sns:ap-southeast-1:123456789012:test_gather")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-southeast-1")
    session = boto3.session.Session()
    sns = session.resource("sns")
    sns.create_topic(Name="test_gather")
    yield sns
    mock.stop()

def test_read_from_dynamodb(_mock_env_dynamodb):
    """Test read from dynamodb function."""
    data = produce.read_from_dynamodb("123")
    assert data == "mock_data"

def test_send_message_to_sns(_mock_env_sns):
    """Test send message to sns function."""
    with open("tests/common_test_data/gather_event.json") as f:
        gather_event = ujson.load(f)[0]

    response = produce.send_message_to_sns(gather_event)
    assert "MessageId" in response

def mock_condition(condition, data, gather_event=None):
    """Mock check for condition function."""
    return True

def mock_strategy(*_args, **_kwargs):
    """Mock check for strategy function."""
    return False, 2

def mock_check_signals(*_args, **_kwargs):
    """Mock check signals function."""
    return True

def test_apply_strategy(monkeypatch):
    """Test apply strategy function."""
    monkeypatch.setattr(produce, "check_signals", mock_check_signals)
    with open("tests/common_test_data/gather_event.json") as f:
        gather_event = ujson.load(f)[0]
    monkeypatch.setattr(condition, "have_data", mock_condition)
    monkeypatch.setattr(strategy_mod, "value_increment", mock_strategy)
    strategies = gather_event["strategy"]
    gather_event, stop_scrape = produce.apply_strategy(strategies, gather_event, "mock_data")
    assert gather_event == 2
    assert not stop_scrape