from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportActionModelAdmin

from subjects.models import Cathedra, Faculty, GroupSubject, Subject, SubjectLog
from subjects.forms import GroupSubjectForm


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
        import_id_fields = ('name', 'form_control', 'semester', 'cathedra__name')


@admin.register(Subject)
class SubjectAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    resource_class = SubjectResource
    list_display = (
        'name',
        'id',
        'is_archived',
        'form_control',
        'zet',
        'semester',
        'comment',
        'cathedra',
        'get_faculty',
        'updated_date',
        'created_date',
    )
    list_display_links = ('name',)
    list_filter = (
        'cathedra__faculty__short_name',
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
        'cathedra__faculty__short_name',
    ]
    ordering = [
        'name',
    ]

    def get_faculty(self, obj):
        if obj.cathedra and obj.cathedra.faculty:
            return f'{obj.cathedra.faculty.short_name}'
        else:
            return '---'
    get_faculty.short_description = 'Факультет'


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
        'id',
        'short_name',
        'faculty',
    )
    ordering = [
        'faculty',
        'name',
    ]
    list_filter = (
        'faculty',
    )
    list_display_links = ('name',)


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
    list_display_links = ('name',)


class GroupSubjectResource(resources.ModelResource):

    class Meta:
        model = GroupSubject
        fields = (
            'subjects__name',
            'subjects__form_control',
            'subjects__semester__semester',
            'groups__name',
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
        # 'subjects',
        'get_subject_name',
        'get_semester',
        'groups',
        'id',
        'is_archived',
        'get_subject_form_control',
        'teacher',
        'att_date',
    )
    fields = [
        'subjects',
        'groups',
        'teacher',
        'att_date',
        'comment',
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
        'subjects__name',
    ]
    list_display_links = ('get_subject_name',)
    form_class = GroupSubjectForm

    def get_subject_name(self, obj):
        return f'{obj.subjects.name}'
    get_subject_name.short_description = 'Дисциплина'

    def get_subject_form_control(self, obj):
        return f'{obj.subjects.form_control}'
    get_subject_form_control.short_description = 'Форма контроля'

    def get_semester(self, obj):
        return f'{obj.subjects.semester.semester}'
    get_semester.short_description = 'Семестр'
