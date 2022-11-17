"""Test the different conditions module."""
import strategy.condition as condition
import json

def test_have_data():
    """Test have data condition checker."""
    with open("tests/common_test_data/gather_event.json", "r") as test_f:
        gather_event = json.load(test_f)[0]
    cond = gather_event["strategy"][0]["condition"]
    with open("tests/common_test_data/eatigo_response.json", "r") as test_f:
        data = json.load(test_f)
    condition_pass = condition.have_data(cond, data)
    assert condition_pass

    data = {
        "result": {
            "result": []
        }
    }
    cond.pop("json_path")
    data = []
    condition_pass = condition.have_data(cond, data)
    assert not condition_pass

    data = {
        "result": {
            "result": []
        }
    }
    cond["json_path"] = "$.result.result[0].name"
    data = []
    condition_pass = condition.have_data(cond, data)
    assert not condition_pass

def test_none():
    """Test none condition."""
    checks = condition.none("mock_condition", "mock_data")
    assert checks

def test_no_data():
    """Test have data condition checker."""
    with open("tests/common_test_data/gather_event.json", "r") as test_f:
        gather_event = json.load(test_f)[0]
    cond = gather_event["strategy"][0]["condition"]
    with open("tests/common_test_data/eatigo_response.json", "r") as test_f:
        data = json.load(test_f)
    condition_pass = condition.no_data(cond, data)
    assert not condition_pass

    data = {
        "result": {
            "result": []
        }
    }
    cond.pop("json_path")
    data = []
    condition_pass = condition.no_data(cond, data)
    assert condition_pass

    data = {
        "meta": {
            "hasMore": False
        }
    }
    cond["json_path"] = "$.meta.hasMore"
    condition_pass = condition.no_data(cond, data)
    assert condition_pass

def test_status_code():
    """Test status code condition."""
    cond = {
        "value": 200
    }
    checks = condition.status_code(
        cond,
        "mock_data",
        gather_event={"response_status_code": 200}
    )
    assert checks

    checks = condition.status_code(
        cond,
        "mock_data",
        gather_event={"response_status_code": 403}
    )
    assert not checks