"""Test initiator handler module."""
import ujson
import initiator.handler_sqs as handler

def test_main(monkeypatch, capsys):
    """Test main handler function."""
    with open("tests/initiator/test_data/sqs_event.json") as f:
        message = ujson.load(f)
    monkeypatch.setattr(handler, "Gather", MockGather)
    event = {
        "Records": [
            {
                "body": ujson.dumps(message)
            }
        ]
    }
    response = handler.main(event, "mock_context")

    captured = capsys.readouterr().out
    assert str(message["initiator"][0]) not in captured
    assert str(message["initiator"][1]) in captured

class MockGather():
    def __init__(self, gather_message, initiator_message):
        """Initiate mock gather class."""
        print(gather_message)

    def process(self):
        pass

def test_validate_message(monkeypatch):
    """Test validate message function."""
    monkeypatch.setattr(handler, "Gather", MockGather)

    with open("tests/initiator/test_data/sqs_event.json") as f:
        message = ujson.load(f)
    assert handler.validate_message(message)

    message["initiator"] = []
    assert not handler.validate_message(message)

    message["initiator"] = ["mock_message"]
    message["sns_event_type"] = "gather"
    assert not handler.validate_message(message)
