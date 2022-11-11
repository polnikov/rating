from import_export import resources
from import_export.admin import ImportExportActionModelAdmin

from django.contrib import admin

from groups.models import Group
from groups.forms import GroupForm


class GroupResource(resources.ModelResource):

    class Meta:
        model = Group
        fields = (
            'name',
            'direction',
            'profile',
            'level',
            'code',
            'is_archived',
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = False


@admin.register(Group)
class GroupAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    resource_class = GroupResource
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
