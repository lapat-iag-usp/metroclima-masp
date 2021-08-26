from django.contrib import admin

from .models import Instrument, Station, Image


class StationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'latitude', 'longitude', 'elevation')
    ordering = ['name']


class InstrumentAdmin(admin.ModelAdmin):
    list_display = ('instrument', 'measuring')
    ordering = ['instrument']


class ImageAdmin(admin.ModelAdmin):
    list_display = ('alt', 'image', 'panoramic')
    ordering = ['image']


admin.site.register(Station, StationAdmin)
admin.site.register(Instrument, InstrumentAdmin)
admin.site.register(Image, ImageAdmin)
