"""Test all the different strategies available."""
import pytest
import ujson
import boto3
from moto import mock_s3
import strategy.strategy as strategy

@pytest.fixture
def _mock_env_s3(monkeypatch):
    """Mock environment for s3 unit test functions."""
    monkeypatch.setenv("REGION_NAME", "ap-southeast-1")
    monkeypatch.setenv("STAGE", "dev")
    monkeypatch.setenv("COUNTRY_CODE", "hk")
    monkeypatch.setenv("VCI_BUCKET", "fp-apac-vci-gaia-rover-condition-ap-southeast-1-dev")
    mock = mock_s3()
    mock.start()
    s3 = boto3.client("s3")
    s3.create_bucket(
        Bucket="fp-apac-vci-gaia-rover-condition-ap-southeast-1-dev",
        CreateBucketConfiguration={
            "LocationConstraint": "ap-southeast-1",
        }
    )
    s3.put_object(
        Bucket="fp-apac-vci-gaia-rover-condition-ap-southeast-1-dev",
        Key="hk/ubereats_latlong_list.json",
        Body=ujson.dumps({"latlong": ["22.193,114.019","22.194,114.020"]})
    )
    s3.put_object(
        Bucket="fp-apac-vci-gaia-rover-condition-ap-southeast-1-dev",
        Key="hk/latlong_list.json",
        Body=ujson.dumps({"latlong": ["default_lat,default_lng"]})
    )
    yield s3
    mock.stop()

def test_value_increment():
    """Test value increment strategy."""
    with open("tests/common_test_data/gather_event.json", "r") as test_f:
        gather_event = ujson.load(test_f)[0]
    strat = gather_event["strategy"][0]
    _stop_scrape, gather_event = strategy.value_increment(gather_event, strat, "mock_data")
    assert gather_event["variables"]["page"] == 2

def test_set_value():
    """Test set value strategy."""
    with open("tests/common_test_data/gather_event.json", "r") as test_f:
        gather_event = ujson.load(test_f)[0]

    strat = {
        "method": "set_value",
        "target": ["page"],
        "condition": {
            "method": "no_data",
            "json_path": "$.result"
        },
        "value": 0
    }

    _stop_scrape, gather_event = strategy.set_value(gather_event, strat, "mock_data")
    assert gather_event["variables"]["page"] == 0

def test_geolocation(_mock_env_s3):
    """Test geolocation strategy."""
    with open("tests/common_test_data/gather_event.json", "r") as test_f:
        gather_event = ujson.load(test_f)[0]
    gather_event["variables"]["latitude"] = "22.193"
    gather_event["variables"]["longitude"] = "114.019"

    strat = {
        "method": "geolocation",
        "target": ["latitude", "longitude"],
        "condition": {
            "method": "have_data",
            "json_path": "$.result.result"
        },
        "type": "s3",
        "value": "hk/ubereats_latlong_list.json"
    }
    _stop_scrape, gather_event = strategy.geolocation(gather_event, strat, "mock_data")
    assert gather_event["variables"]["latitude"] == "22.194"
    assert gather_event["variables"]["longitude"] == "114.020"


def test_retrieve_data():
    """Test retrieve data strategy."""
    with open("tests/common_test_data/gather_event.json", "r") as test_f:
        gather_event = ujson.load(test_f)[0]
    strat = {
        "target": ["offset"],
        "condition": "none",
        "json_path": "$.meta.offset",
        "default": 0
    }
    gather_event["strategy"] = strat
    gather_event["variables"] = {
        "offset": 0
    }
    data = {
        "meta": {
            "offset": 25
        }
    }
    _stop_scrape, gather_event = strategy.retrieve_data(gather_event, strat, data)
    assert gather_event["variables"]["offset"] == 25

    data = {
    }
    _stop_scrape, gather_event = strategy.retrieve_data(gather_event, strat, data)
    assert gather_event["variables"]["offset"] == 0
