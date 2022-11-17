"""Module to test gather class."""
import os
import time
import pytest
import ujson
import boto3
from moto import mock_dynamodb2, mock_sns
import initiator.gather.gather as gather


@pytest.fixture
def _mock_env_sns(monkeypatch):
    """Mock environment for sns unit test functions."""
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-southeast-1")
    mock = mock_sns()
    mock.start()
    session = boto3.session.Session(region_name="ap-southeast-1")
    sns = session.resource("sns")
    sns.create_topic(Name="test_topic")
    yield sns
    mock.stop()

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
    yield dynamodb
    mock.stop()

def test_create_variables(_mock_env_dynamodb, _mock_env_sns):
    """Test create variables function of gather class."""
    with open("tests/initiator/test_data/sqs_event.json") as f:
        message = ujson.load(f)
    with open("tests/common_test_data/eatigo_response.json", "r") as test_f:
        data = ujson.load(test_f)["result"]["result"]
    initiator_message = message["initiator"].pop(0)
    process = gather.Gather(message, initiator_message)
    variables = process.create_variables(data[0], initiator_message["variables"])
    assert variables == {
        "menu_id": "1231",
        "page": 1
    }

def mock_uuid():
    """Mock uuid function."""
    return "mock_uuid"

def mock_time():
    """Mock time function."""
    return "123"

def test_process(_mock_env_dynamodb, _mock_env_sns, monkeypatch):
    """Test create variables function of gather class."""
    with open("tests/initiator/test_data/sqs_event.json") as f:
        message = ujson.load(f)
    with open("tests/common_test_data/eatigo_response.json", "r") as test_f:
        data = ujson.load(test_f)
    initiator_message = message["initiator"].pop(0)

    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-southeast-1")
    monkeypatch.setenv("SNS_GATHER", "arn:aws:sns:ap-southeast-1:123456789012:test_topic")
    dynamodb = boto3.resource("dynamodb")
    dynamodb = dynamodb.Table("test_data_table")
    dynamodb.put_item(
        Item={
                "hash_id": "123",
                "data": data
        }
    )
    monkeypatch.setattr(gather, "uuid4", mock_uuid)
    process = gather.Gather(message, initiator_message)
    monkeypatch.setattr(time, "time", mock_time)
    response, _sns_response = process.process()
    assert response == {
        'sns_event_type': 'gather',
        'scraper_type': 'api',
        'scraping_type': 'menu',
        'scope': {
            'url': 'https://www.eatigo.com?menu={[menu_id]}',
            'method': 'GET'
        },
        'variables': {
            'page': 1,
            'menu_id': '20'
        },
        'strategy': [],
        'current_lambda': 'scraper1',
        'service_name': 'eatigo',
        'country_code': 'hk',
        'scraped_data_hash': '123',
        'initiator': [
            {
                'scraping_type': 'grocery',
                'initiator_method': 'list_iteration',
                'json_path': '$.result.items',
                'scope': {
                    'url': 'https://www.eatigo.com?item={[item_id]}',
                    'method': 'GET'
                },
                'variables': {
                    'item_id': {'method': 'json_path', 'json_path': '$.id'},
                    'page': {'method': 'set_value', 'value': 1}
                },
                'mapper_config': [{'entity_type': 'grocery', 'value': {'key': 'datamapping/v2/eatigo_grocery.json'}}]
            }
        ],
        'mapper_config': [{'entity_type': 'menu', 'value': {'key': 'datamapping/v2/eatigo_menu.json'}}],
        'process_id': 'mock_uuid',
        "initiation_metadata": {
            'timestamp': 123,
            'variables': {'menu_id': '20', 'page': 1}
        }
    }

def test_grouped_process(_mock_env_dynamodb, _mock_env_sns, monkeypatch):
    """Test create variables function of gather class."""
    with open("tests/initiator/test_data/sqs_event.json") as f:
        message = ujson.load(f)
    with open("tests/common_test_data/eatigo_response.json", "r") as test_f:
        data = ujson.load(test_f)
    initiator_message = message["initiator"].pop(0)
    initiator_message["group_length"] = 3
    initiator_message["variables"]["menu_id"] = [
        {
            "method": "json_path",
            "json_path": "$[*].id"
        },
        {
            "method": "type_convert",
            "value": "list"
        }
    ]

    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-southeast-1")
    monkeypatch.setenv("SNS_GATHER", "arn:aws:sns:ap-southeast-1:123456789012:test_topic")
    dynamodb = boto3.resource("dynamodb")
    dynamodb = dynamodb.Table("test_data_table")
    dynamodb.put_item(
        Item={
                "hash_id": "123",
                "data": data
        }
    )
    monkeypatch.setattr(gather, "uuid4", mock_uuid)
    process = gather.Gather(message, initiator_message)
    monkeypatch.setattr(time, "time", mock_time)
    response, _sns_response = process.process()
    assert response == {
        'sns_event_type': 'gather',
        'scraper_type': 'api',
        'scraping_type': 'menu',
        'scope': {
            'url': 'https://www.eatigo.com?menu={[menu_id]}',
            'method': 'GET'
        },
        'variables': {
            'page': 1,
            'menu_id': ['19', '20']
        },
        'strategy': [],
        'current_lambda': 'scraper1',
        'service_name': 'eatigo',
        'country_code': 'hk',
        'scraped_data_hash': '123',
        'initiator': [
            {
                'scraping_type': 'grocery',
                'initiator_method': 'list_iteration',
                'json_path': '$.result.items',
                'scope': {
                    'url': 'https://www.eatigo.com?item={[item_id]}',
                    'method': 'GET'
                },
                'variables': {
                    'item_id': {'method': 'json_path', 'json_path': '$.id'},
                    'page': {'method': 'set_value', 'value': 1}
                },
                'mapper_config': [{'entity_type': 'grocery', 'value': {'key': 'datamapping/v2/eatigo_grocery.json'}}]
            }
        ],
        'mapper_config': [{'entity_type': 'menu', 'value': {'key': 'datamapping/v2/eatigo_menu.json'}}],
        'process_id': 'mock_uuid',
        'initiation_metadata': {
            'timestamp': 123,
            'variables': {
                'menu_id': ["19", "20"],
                'page': 1
            }
        }
    }
