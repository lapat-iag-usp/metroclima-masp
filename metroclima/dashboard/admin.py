from django.contrib import admin
from django.db import models
from django.forms import Textarea

from .models import Campaign,  CampaignFile,\
                    Flag, \
                    Event, EventFile,\
                    Logbook, Video


class CampaignFileInline(admin.TabularInline):
    model = CampaignFile


class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'station', 'instrument')
    ordering = ['name', 'station', 'instrument']
    readonly_fields = ('name', 'slug',)
    inlines = [CampaignFileInline]

    class Media:
        js = ('/static/admin/js/hide_attribute_campaign.js',)


class EventFileInline(admin.TabularInline):
    model = EventFile


class EventAdmin(admin.ModelAdmin):
    readonly_fields = ('name', 'slug',)
    list_display = ('name', 'event_date', 'description', 'invalid', 'start_date', 'end_date', 'flags', 'revised')
    fields = ['name', 'logbook', 'event_date', 'description', 'invalid', 'start_date', 'end_date', 'flags', 'revised']
    list_filter = ('logbook', 'event_date', 'invalid', 'revised', 'flags')
    inlines = [EventFileInline]

    class Media:
        js = ('/static/admin/js/hide_attribute.js',)


# class EventInline(admin.TabularInline):
#     model = Event
#     fields = ['event_date', 'description', 'invalid', 'start_date', 'end_date', 'flags', 'revised']
#     ordering = ['event_date']
#     formfield_overrides = {
#         models.TextField: {'widget': Textarea(attrs={'rows': 6, 'cols': 40})},
#     }
#     show_change_link = True


class LogbookAdmin(admin.ModelAdmin):
    readonly_fields = ('name', 'slug',)
    # inlines = [EventInline]


class FlagAdmin(admin.ModelAdmin):
    list_display = ('flag', 'description')
    ordering = ['flag']


admin.site.register(Campaign, CampaignAdmin)
admin.site.register(Flag, FlagAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Logbook, LogbookAdmin)
admin.site.register(Video)
