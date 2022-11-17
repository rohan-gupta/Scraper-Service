"""Test the different conditions module."""
from strategy.geolocation import Geolocation, S3Geolocation 
import json_type.signal as signal
import pytest
import boto3
from moto import mock_s3
import ujson

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

def test_s3_geolocation(_mock_env_s3):
    """Initiate test."""
    latitude = 22.193
    longitude = 114.019
    strategy = {
        "method": "geolocation",
        "target": ["latitude", "longitude"],
        "condition": {
            "method": "have_data",
            "json_path": "$.result.result"
        },
        "type": "s3",
        "value": "hk/ubereats_latlong_list.json"
    }
    Geo = S3Geolocation(latitude, longitude, strategy)
    assert Geo.get_latitude() == latitude
    assert Geo.get_longitude() == longitude
    next_latlng = Geo.get_lat_lng()
    assert next_latlng == "22.194,114.020"

    latitude = 22.194
    longitude = 114.020
    Geo = S3Geolocation(latitude, longitude, strategy)
    next_latlng = Geo.get_lat_lng()
    assert next_latlng == "22.193,114.019"

    strategy["value"] = "sg/latlong_list.json"
    Geo = S3Geolocation(latitude, longitude, strategy)
    next_latlng = Geo.get_lat_lng()
    assert next_latlng == "default_lat,default_lng"
