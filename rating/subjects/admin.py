from django.contrib import admin
from subjects.models import Cathedra, Faculty, GroupSubject, Subject, SubjectLog
from import_export import resources
from import_export.admin import ImportExportActionModelAdmin


class SubjectResource(resources.ModelResource):

    class Meta:
        model = Subject
        fields = (
            'id',
            'name',
            'form_control',
            'zet',
            'semester',
            'cathedra__name',
            'is_archived',
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('name', 'form_control', 'semester')


@admin.register(Subject)
class SubjectAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    resource_class = SubjectResource
    list_display = (
        'id',
        'name',
        'is_archived',
        'form_control',
        'zet',
        'semester',
        'cathedra',
        'comment',
        'updated_date',
        'created_date',
    )
    list_display_links = ('name',)
    list_filter = (
        'is_archived',
        'cathedra',
        'form_control',
        'semester',
        'name',
    )
    fields = [
        ('name', 'cathedra'),
        ('form_control', 'semester', 'zet'),
        'comment',
        'is_archived',
    ]
    search_fields = [
        'name',
        'cathedra',
        'form_control',
    ]
    list_editable = [
        'comment',
        'is_archived',
    ]
    ordering = [
        'name',
    ]

########################################################################################################################


@admin.register(SubjectLog)
class SubjectLog(admin.ModelAdmin):
    list_display = (
        'user',
        'record_id',
        'field',
        'old_value',
        'new_value',
        'timestamp',
    )
    ordering = [
        '-timestamp',
    ]
    list_filter = (
        'user',
        'field',
    )

########################################################################################################################


class CathedraResource(resources.ModelResource):

    class Meta:
        model = Cathedra
        fields = (
            'id',
            'name',
            'short_name',
            'faculty__name',
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('name', 'short_name', 'faculty__name')


@admin.register(Cathedra)
class CathedraAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    resource_class = CathedraResource
    list_display = (
        'name',
        'short_name',
        'faculty',
    )
    list_editable = [
        'faculty',
    ]
    ordering = [
        'faculty',
        'name',
    ]
    list_filter = (
        'faculty',
    )

########################################################################################################################


class FacultyResource(resources.ModelResource):

    class Meta:
        model = Faculty
        fields = (
            'id',
            'name',
            'short_name',
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('name', 'short_name')


@admin.register(Faculty)
class FacultyAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    resource_class = FacultyResource
    list_display = (
        'name',
        'short_name',
    )

########################################################################################################################


class GroupSubjectResource(resources.ModelResource):

    class Meta:
        model = Subject
        fields = (
            'groups',
            'subjects',
            'teacher',
            'att_date',
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = False


@admin.register(GroupSubject)
class GroupSubjectAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    resource_class = GroupSubjectResource
    list_display = (
        'id',
        'subjects',
        'is_archived',
        'get_subject_name',
        'groups',
        'get_semester',
        'get_subject_form_control',
        'teacher',
        'att_date',
    )
    fields = [
        'subjects',
        'groups',
        'is_archived',
    ]
    ordering = [
        'subjects',
    ]
    list_filter = (
        'groups',
        'teacher',
        'att_date',
    )
    search_fields = [
        'subjects',
    ]
    list_editable = [
        'is_archived',
    ]
    list_display_links = ('id',)

    def get_subject_name(self, obj):
        return f'{obj.subjects.name}'
    get_subject_name.short_description = 'Дисциплина'

    def get_subject_form_control(self, obj):
        return f'{obj.subjects.form_control}'
    get_subject_form_control.short_description = 'Форма контроля'

    def get_semester(self, obj):
        return f'{obj.subjects.semester.semester}'
    get_semester.short_description = 'Семестр'
