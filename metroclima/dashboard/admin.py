from django.contrib import admin

from .models import Campaign


class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'station', 'instrument')
    ordering = ['name', 'station', 'instrument']


admin.site.register(Campaign, CampaignAdmin)
