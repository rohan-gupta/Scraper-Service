"""Test module for json scraper handler."""
import json
import json_type.handler as handler

def test_main(monkeypatch):
    """Test main handler for json scraper."""
    event = {
        "Records": [{
            "body": json.dumps({
                "sns_event_type": "gather",
                "scraper_type": "api",
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
            })
        }]
    }
    context = ""
    monkeypatch.setattr(handler, "start_scrape", mock_start_scrape)
    response = handler.main(event, context)
    assert response == "Scraping has finished"
    event = {
        "Records": [{
            "body": '"data_type": "html"'
        }]
    }
    response = handler.main(event, context)

    assert response == "Message not processed"

def test_validate_message():
    """Test validate message."""
    message = json.dumps({
                "sns_event_type": "gather",
                "scraper_type": "api",
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
            })

    process_message = handler.validate_message(message)

    assert process_message

    html_message = json.dumps({
                "sns_event_type": "gather",
                "data_type": "html",
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
                }
            })
    process_message = handler.validate_message(html_message)

    assert not process_message

    rogue_message = "test_message"
    process_message = handler.validate_message(rogue_message)

    assert not process_message

    with open("tests/json/test_data/test_incomplete_messages.json") as f:
        messages = json.load(f)
        for message in messages:
            process_message = handler.validate_message(json.dumps(message))
            assert not process_message

def mock_start_scrape(*_args, **_kwargs):
    """Mock start scraping function."""
    return "scraping finished"