from django.contrib import admin

from .models import Group, Member, Institution


class GroupAdmin(admin.ModelAdmin):
    list_display = ('group', 'order')
    ordering = ['order']
    list_editable = ('order',)


class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution', 'group')
    ordering = ['name', 'institution', 'group']


admin.site.register(Group, GroupAdmin)
admin.site.register(Institution)
admin.site.register(Member, MemberAdmin)
