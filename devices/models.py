import logging
import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone
from django_admin_geomap import GeoItem
from geoposition.fields import GeopositionField
from geoposition import Geoposition

from .device_management import ttn_registration, get_ttn_details

from opentelemetry import trace

tracer = trace.get_tracer(__name__)

import what3words
from metrics import Metrics

logger = logging.getLogger(__name__)

# Create your models here.
class Device(models.Model, GeoItem):
    macaddress = models.CharField(max_length=16)
    name = models.CharField(max_length=100)
    w3w_location = models.CharField(max_length=255, null=True, default=None)
    geolocation = GeopositionField()
    ttn_dev_eui = models.CharField(max_length=100, null=True, default=None, blank=True)
    is_active = models.BooleanField(default=False)
    deployed_at = models.DateTimeField(null=True)
    last_seen = models.DateTimeField(null=True)

    __orig_w3w = None
    __orig_geoloc = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__orig_w3w = self.w3w_location
        self.__orig_geoloc = self.geolocation

    @property
    def geoloc(self):
        geocoder = what3words.Geocoder(settings.W3W_API_KEY)
        if self.geolocation.latitude is None or self.geolocation.latitude == 0:
            with tracer.start_as_current_span("what3words_lookup_new_geolocation"):
                logger.info(
                    f"Geo-coordinates not found for {self.name}, retrieving from W3W"
                )
                res = geocoder.convert_to_coordinates(self.w3w_location)
                Metrics.w3w_api_calls.inc()
                self.geolocation = Geoposition(
                    float(res["coordinates"]["lat"]), float(res["coordinates"]["lng"])
                )
                self.save()
                return res
        else:
            ret_data = {
                "coordinates": {
                    "lat": self.geolocation.latitude,
                    "lng": self.geolocation.longitude,
                }
            }
            return ret_data

    @property
    def geomap_longitude(self):
        return (
            ""
            if self.geoloc["coordinates"]["lng"] is None
            else str(self.geoloc["coordinates"]["lng"])
        )

    @property
    def geomap_latitude(self):
        return (
            ""
            if self.geoloc["coordinates"]["lat"] is None
            else str(self.geoloc["coordinates"]["lat"])
        )

    @property
    def geomap_popup_view(self):
        return "<p><strong>Name: </strong>{}</p><p><strong>Last Seen: </strong>{}</p>".format(
            str(self.name), str(self.last_seen)
        )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.ttn_dev_eui is None:
            logger.info("Device not found in TTN, registering")
            ttn_details = ttn_registration(
                device_mac=self.macaddress,
                device_name=self.name,
                app_name=settings.TTN_APP_NAME,
                app_key=settings.TTN_APP_KEY,
                auth_token=settings.TTN_ADMIN_KEY,
            )
            self.ttn_dev_eui = ttn_details["dev_eui"]

        if self.w3w_location != self.__orig_w3w:
            with tracer.start_as_current_span("what3words_lookup_w3w_address_change"):
                logger.info(
                    f"W3W address has changed for {self.name}, updating coordinates"
                )
                geocoder = what3words.Geocoder(settings.W3W_API_KEY)
                res = geocoder.convert_to_coordinates(self.w3w_location)
                Metrics.w3w_api_calls.inc()
                self.geolocation = Geoposition(
                    float(res["coordinates"]["lat"]), float(res["coordinates"]["lng"])
                )
                super(Device, self).save(*args, **kwargs)
        if self.geolocation != self.__orig_geoloc:
            with tracer.start_as_current_span("what3words_lookup_coordinates_change"):
                logger.info(f"Coordinates have changed for {self.name}, updating w3w")
                geocoder = what3words.Geocoder(settings.W3W_API_KEY)
                res = geocoder.convert_to_3wa(
                    what3words.Coordinates(
                        self.geolocation.latitude, self.geolocation.longitude
                    )
                )
                Metrics.w3w_api_calls.inc()
                self.w3w_location = res["words"]
                super(Device, self).save(*args, **kwargs)


class MetricType(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    unit = models.CharField(max_length=100)

    def __str__(self):
        return f"{ self.name } ({self.description}) [{self.unit}]"

class DeviceMetric(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    measurement_type = models.ForeignKey(MetricType, on_delete=models.CASCADE)
    measurement = models.FloatField()
    recorded_at = models.DateTimeField(default = timezone.now)
