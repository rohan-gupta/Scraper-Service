import pytest
import boto3
from moto import mock_sns
import json_type.signal as signal

@pytest.fixture
def _mock_env_sns():
    """Mock environment for sns unit test functions."""
    mock = mock_sns()
    mock.start()
    session = boto3.session.Session(region_name="ap-southeast-1")
    sns = session.resource("sns")
    sns.create_topic(Name="test_topic")
    yield sns
    mock.stop()

def test_send_signal(monkeypatch, _mock_env_sns):
    """Test send signal function."""
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-southeast-1")
    monkeypatch.setenv("SNS_SIGNAL", "arn:aws:sns:ap-southeast-1:123456789012:test_topic")
    response = signal.send_signal("init", "mock_ip")
    assert "MessageId" in response