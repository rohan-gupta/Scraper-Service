import time
import json
import requests
import pytest
import boto3
from moto import mock_dynamodb2, mock_sns
from json_type import scrape


def test_replace_variables():
    """Test variables replacement from scope message."""
    url = "http://www.eatigo.com?page={[page]}"
    variables = {
        "page": 1
    }
    values = scrape.replace_variables(url, variables)
    assert values == "http://www.eatigo.com?page=1"

    url = "myurl?count={[count]}"
    with pytest.raises(KeyError) as _e:
        values = scrape.replace_variables(url, variables)

    method = "GET"
    values = scrape.replace_variables(method, variables)
    assert values == "GET"

    headers = {
        "User-Agent": "Mozilla 5.0",
        "page": "{[page]}"
    }
    values = scrape.replace_variables(headers, variables)
    assert values == {**headers, "page": 1}

    data = {
        "location": {
            "lat": "{[latitude]}",
            "lng": "{[longitude]}"
        }
    }
    variables["latitude"] = "1.23"
    variables["longitude"] = "103.2"
    values = scrape.replace_variables(data, variables)
    assert data == {
        "location": {
            "lat": "1.23",
            "lng": "103.2"
        }
    }

def test_construct_request_object(monkeypatch):
    """Test request object construction from scope message."""
    request_details = {
        "url": "http://www.eatigo.com?page={[page]}",
        "method": "GET"
    }
    variables = {
        "page": 1
    }
    monkeypatch.setattr(scrape, "get_web_browser_user_agent", mock_get_user_agent)
    request_object = scrape.construct_request_object(request_details, variables)
    assert request_object == {
        "url": "http://www.eatigo.com?page=1",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla"}
    }

def mock_get_user_agent(*_args, **_kwargs):
    """Mock get user agent function."""
    return {"userAgent": "Mozilla"}

def test_start_scrape(monkeypatch, capsys, _mock_env_dynamodb, _mock_env_sns):
    """Test scraping function."""
    with open("tests/common_test_data/gather_event.json") as f:
        message = json.load(f)

    monkeypatch.setattr(scrape, "send_signal", mock_send_signal)
    monkeypatch.setattr(scrape, "send_scraping_request", mock_send_scraping_request)
    monkeypatch.setattr(requests, "get", mock_requests_response)
    monkeypatch.setattr(scrape, "get_web_browser_user_agent", mock_get_user_agent)

    response = scrape.start_scrape(message[0])
    assert response == "Done"
    captured = capsys.readouterr().out
    assert "start" in captured
    assert "end" in captured

def mock_send_signal(type, *_args, **_kwargs):
    """Mock sending signal function."""
    print(f"{type} {time.time()}")

def mock_send_scraping_request(type, *_args, **_kwargs):
    """Mock sending scraping request."""
    return "mock_data", {"cookies": "dummy data"}, 200

def mock_requests_response(*_args, **_kwargs):
    """Mock response from requests object."""
    return MockRequests('tests/common_test_data/ip_response.json')

class MockRequests():
    """Mock request class."""
    def __init__(self, filepath):
        """Initialize class."""
        self.status_code = 200
        self.text = open(filepath, 'r').read()

def mock_uuid():
    """Mock uuid function."""
    return "mock_uuid"


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

@pytest.fixture
def _mock_env_sns(monkeypatch):
    """Mock environment for sns unit test functions."""
    mock = mock_sns()
    mock.start()
    monkeypatch.setenv("SNS_SIGNAL", "arn:aws:sns:ap-southeast-1:123456789012:test_signal")
    monkeypatch.setenv("SNS_PRODUCE", "arn:aws:sns:ap-southeast-1:123456789012:test_produce")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-southeast-1")
    session = boto3.session.Session()
    sns = session.resource("sns")
    sns.create_topic(Name="test_signal")
    sns.create_topic(Name="test_produce")
    yield sns
    mock.stop()

def test_create_produce_event(monkeypatch, _mock_env_dynamodb, mocker):
    """Test create produce event function."""
    monkeypatch.setattr(scrape, "uuid4", mock_uuid)
    with open("tests/common_test_data/gather_event.json") as f:
        gather_event = json.load(f)[0]
    scraped_data = {
        "result": "restaurants"*18000000,
        "status": 200
    }
    cookies = {"cookies": "dummy data"}
    spy = mocker.spy(scrape, "save_data")
    produce_event = scrape.create_produce_event(gather_event, scraped_data, cookies, 200)
    spy.assert_called_with({"result": "restaurants"*18000000, "status": 200}, {"cookies": "dummy data"})
    assert produce_event == {
        **gather_event,
        "scraped_data_hash": "mock_uuid,mock_uuid",
        "sns_event_type": "produce",
        "response_status_code": 200
    }

def test_get_partitions_from_size():
    """Test get partitions based on size function."""
    data = "A"*370000 + "B"*370000 + "C"*10040
    partitions = scrape.get_partition_from_size(data)
    assert len(partitions) == 3
    assert len(partitions[2]) == 10040
    assert partitions[2] == "C"*10040