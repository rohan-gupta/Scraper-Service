"""Module to test functions in save.py."""
import json
import uuid
import ports.publish as publish

def test_publish_options():
    """Test publish options function."""
    data = {
        "result": "scraped_data"
    }
    option = publish.publish_options(data)
    assert option == "dynamodb"

def test_publish_data(monkeypatch):
    """Test publish data function."""
    gather_event = {
        "sns_event_type": "gather",
        "data_type": "json",
        "scraping_type": "restaurants",
        "scope": {
            "url": "http://www.eatigo.com?page={page}",
            "method": "GET"
        },
        "variables": {
            "page": 1
            },
        "strategy": {
            "increment": {
                "target": ["page"],
                "condition": "have_data"
            }
        },
        "service_name": "eatigo",
        "country_code": "hk"
    }

    scraped_data = {
        "result": "scraped_data"
    }
    option = "dynamodb"
    monkeypatch.setattr(publish, "uuid4", mock_uuid_generation)
    event_message = publish.create_produce_event(scraped_data, gather_event, option)
    assert event_message == {
        "partition_key": "eatigo|hk",
        "sort_key": "mock_uuid",
        "options": "dynamodb"
    }

def mock_uuid_generation():
    """Mock uuid generation function."""
    return "mock_uuid"

def test_construct_sns_message():
    """Test construct sns message function."""
    gather_event = "mock_gather_event"
    produce_event = "mock_produce_event"
    event_message = publish.construct_sns_message(gather_event, produce_event)
    assert event_message == json.dumps({
        "gather_event": gather_event,
        "produce_event": produce_event
    })