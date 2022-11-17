"""Test module for initiator methods."""
import pytest
import yaml
import ujson
import boto3
from moto import mock_s3
import initiator.initiator as initiator

@pytest.fixture
def _mock_env_s3(monkeypatch):
    """Mock environment for s3 unit test functions."""
    monkeypatch.setenv("REGION_NAME", "ap-southeast-1")
    monkeypatch.setenv("STAGE", "dev")
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
    with open("tests/initiator/test_data/eatigo_config.yml") as f:
        test_data = f.read()
    s3.put_object(
        Bucket="fp-apac-vci-gaia-rover-condition-ap-southeast-1-dev",
        Key="config/eatigo_restaurants_api.yml",
        Body=test_data
    )
    yield s3
    mock.stop()

def test_methods_factory():
    """Test methods factory to check it returns proper method."""
    method_type = "config"
    assert initiator.initiator_factory(method_type) == initiator.config

def test_config(_mock_env_s3):
    """Test config method of initiator."""
    message = {
        "sns_event_type": "initiation",
        "initiator_type": "config",
        "path": "config/eatigo_restaurants_api.yml"
    }
    gather_event = initiator.config(message)
    with open("tests/initiator/test_data/eatigo_config.yml") as f:
        expected = yaml.safe_load(f)
    assert gather_event == expected

def test_message():
    """Test message method of initiator."""
    message = {
        "sns_event_type": "initiation",
        "initiator_type": "message"
    }
    with open("tests/initiator/test_data/eatigo_config.yml") as f:
        message["message"] = yaml.safe_load(f)
    gather_event = initiator.message(message)
    assert gather_event == message["message"]
