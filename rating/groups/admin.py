from import_export import resources
from import_export.admin import ImportExportActionModelAdmin

from django.contrib import admin

from groups.models import Group
from groups.forms import GroupForm


class GroupResource(resources.ModelResource):

    class Meta:
        model = Group
        fields = (
            'id',
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
        import_id_fields = ('name', 'direction', 'profile', 'level')


@admin.register(Group)
class GroupAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    resource_class = GroupResource
    list_display = (
        'name',
        'id',
        'is_archived',
        'direction',
        'profile',
        'level',
        'code',
        'created_date',
        'updated_date',
    )
    list_display_links = ('name',)
    list_filter = ('is_archived', 'level', 'code')
    fields = [
        'name',
        'direction',
        'profile',
        'level',
        'code',
        'is_archived',
    ]
    ordering = [
        'level',
        'code',
    ]
    readonly_fields = ('created_date', 'updated_date')
    form = GroupForm
