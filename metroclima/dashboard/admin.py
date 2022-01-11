from django.contrib import admin

from .models import Campaign


class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'station', 'instrument')
    ordering = ['name', 'station', 'instrument']
    readonly_fields = ('name', 'slug',)

    class Media:
        js = ('/static/admin/js/hide_attribute_campaign.js',)


admin.site.register(Campaign, CampaignAdmin)
