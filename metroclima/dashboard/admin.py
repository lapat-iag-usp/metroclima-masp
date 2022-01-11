from django.contrib import admin

from .models import Campaign,  CampaignFile


class CampaignFileInline(admin.TabularInline):
    model = CampaignFile


class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'station', 'instrument')
    ordering = ['name', 'station', 'instrument']
    readonly_fields = ('name', 'slug',)
    inlines = [CampaignFileInline]

    class Media:
        js = ('/static/admin/js/hide_attribute_campaign.js',)


admin.site.register(Campaign, CampaignAdmin)
