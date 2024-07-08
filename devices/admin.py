from django.contrib import admin

# Register your models here.

from django_admin_geomap import ModelAdmin

from .models import *


class DeviceAdmin(admin.ModelAdmin):

    list_display = (
            "name",
            "last_seen"
            )

class MetricTypeAdmin(admin.ModelAdmin):
    pass

class DeviceMetricAdmin(admin.ModelAdmin):
    pass

admin.site.register(Device, DeviceAdmin)
admin.site.register(MetricType, MetricTypeAdmin)
admin.site.register(DeviceMetric, DeviceMetricAdmin)
