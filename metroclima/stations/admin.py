from django.contrib import admin

from .models import Instrument, InstrumentFile, \
                    Station, Image


class StationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'latitude', 'longitude', 'elevation')
    ordering = ['name']


class InstrumentFileInline(admin.TabularInline):
    model = InstrumentFile


class InstrumentAdmin(admin.ModelAdmin):
    list_display = ('instrument', 'serial_number', 'measuring')
    ordering = ['instrument']
    inlines = [InstrumentFileInline]


class ImageAdmin(admin.ModelAdmin):
    list_display = ('alt', 'image', 'panoramic')
    ordering = ['image']


admin.site.register(Station, StationAdmin)
admin.site.register(Instrument, InstrumentAdmin)
admin.site.register(Image, ImageAdmin)
