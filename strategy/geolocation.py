from abc import ABC, abstractmethod
import os
import boto3
import ujson

class Geolocation(ABC):
    """Base clase for geolocation strategy."""
    def __init__(self, latitude, longitude, strategy):
        """Initiate class."""
        self.strategy = strategy
        self.latitude = latitude
        self.longitude = longitude
    
    @abstractmethod
    def get_lat_lng(self):
        """Abstract method to get next lat lng."""
        pass

    def default_get_lat_lng(self):
        """Default method to get lat lng in case it fails."""
        s3 = boto3.resource("s3")
        try:
            default_filepath = f"{os.getenv('COUNTRY_CODE')}/latlong_list.json"
            s3_object = s3.Object(
                f"{os.getenv('VCI_BUCKET')}",
                default_filepath
            )
            latlng_list = ujson.load(s3_object.get()["Body"])["latlong"]
            next_lat_lng = self.get_next_lat_lng_list(latlng_list)
        except Exception as ex:
            message = f"Error:{ex}"
            print(message)
            next_lat_lng = None
        return next_lat_lng

    def get_next_lat_lng_list(self, latlng_list):
        """Get next lat lng from a list based on current lat lng."""
        latlng_list = sorted(list(set(latlng_list)))
        try:
            current_index = latlng_list.index(f"{self.latitude},{self.longitude}")
        except ValueError:
            current_index = -1
        try:
            next_latlng = latlng_list[current_index+1]
        except IndexError:
            next_latlng = latlng_list[0]
        return next_latlng

    def get_latitude(self):
        """Get latitude value."""
        return self.latitude

    def get_longitude(self):
        """Get longitude value."""
        return self.longitude

class S3Geolocation(Geolocation):
    """Getting geolocation from s3."""
    def get_lat_lng(self):
        """Implement getting next lat long from s3."""
        s3 = boto3.resource("s3")
        try:
            filepath = self.strategy["value"]
            s3_object = s3.Object(
                f"{os.getenv('VCI_BUCKET')}",
                filepath
            )
            latlng_list = ujson.load(s3_object.get()["Body"])["latlong"]
            next_latlng = self.get_next_lat_lng_list(latlng_list)

        except Exception as ex:
            message = f"Error:{ex}"
            print(message)
            next_latlng = self.default_get_lat_lng()
        return next_latlng

def geolocation_factory(method_type):
    """Function to retrieve which method to use."""
    methods = {
        "s3": S3Geolocation
    }
    return methods[method_type]