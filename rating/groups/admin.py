from django.contrib import admin

from groups.models import Group
from groups.forms import GroupForm


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'is_archived',
        'direction',
        'profile',
        'level',
        'code',
        'created_date',
        'updated_date',
    )
    list_display_links = ('name',)
    fields = [
        'name',
        'direction',
        'profile',
        'level',
        'code',
        'is_archived',
        'created_date',
        'updated_date',
    ]
    ordering = [
        'level',
        'code',
    ]
    readonly_fields = ('created_date', 'updated_date')
    form = GroupForm
