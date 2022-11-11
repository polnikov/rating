from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportActionModelAdmin
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin

from students.forms import ResultForm
from students.models import Basis, Result, Semester, Student, StudentLog

admin.site.site_header = 'Рейтинг ФИЭиГХ'


class StudentResource(resources.ModelResource):

    class Meta:
        model = Student
        fields = (
            'student_id',
            'last_name',
            'first_name',
            'second_name',
            'basis__name',
            'citizenship',
            'level',
            'group__name',
            'semester__semester',
            'start_date',
            'status',
            'tag',
            'money',
            'comment',
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('student_id',)


@admin.register(Student)
class StudentAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    resource_class = StudentResource
    list_display = (
        'fullname',
        'is_archived',
        'student_id',
        'semester',
        'group',
        'semester',
        'status',
        'tag',
        'start_date',
        'money',
        'comment',
        'updated_date',
        'created_date',
    )
    list_filter = (
        'is_archived',
        'semester',
        'group',
        'status',
        'tag',
        'level',
        'basis',
        'citizenship',
    )
    fields = [
        'student_id',
        ('last_name', 'first_name', 'second_name'),
        'citizenship',
        'basis',
        'level',
        'group',
        'semester',
        'start_date',
        'money',
        'status',
        'tag',
        'comment',
        'is_archived',
    ]
    search_fields = [
        'first_name',
        'last_name',
        'student_id',
        'comment',
    ]
    list_editable = [
        'is_archived',
    ]
    ordering = [
        'level',
        '-status',
        'last_name',
    ]
    list_display_links = ('fullname',)


@admin.register(StudentLog)
class StudentLog(admin.ModelAdmin):
    list_display = (
        'user',
        'record_id',
        'field',
        'old_value',
        'new_value',
        'timestamp',
    )
    ordering = ['-timestamp']
    list_filter = (
        'user',
        'field',
    )

########################################################################################################################


class ResultResource(resources.ModelResource):

    class Meta:
        model = Result
        fields = (
            'groupsubject__subjects__name',
            'groupsubject__subjects__form_control',
            'groupsubject__teacher',
            'groupsubject__att_date',
            'students__last_name',
            'students__first_name',
            'students__second_name',
            'groupsubject__groups__name',
            'groupsubject__subjects__semester',
            'mark',
            'tag',
            'is_archived',
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = False


@admin.register(Result)
class ResultAdmin(ImportExportActionModelAdmin, admin.ModelAdmin, DynamicArrayMixin):
    resource_class = ResultResource
    list_display = [
        'id',
        'get_student_name',
        'get_student_group',
        'get_student_semester',
        'get_subject_name',
        'mark',
        'tag',
        'is_archived',
    ]
    fields = [
        'groupsubject',
        'students',
        'mark',
        'tag',
        'is_archived',
    ]
    # search_fields = ['students__fullname',]
    list_filter = (
        'groupsubject__groups__name',
        'tag',
        'mark',
    )
    list_display_links = ('get_student_name',)
    form_class = ResultForm

    def get_student_name(self, obj):
        return f'{obj.students.fullname}'
    get_student_name.short_description = 'Студент'

    def get_student_group(self, obj):
        return f'{obj.groupsubject.groups}'
    get_student_group.short_description = 'Группа'

    def get_subject_name(self, obj):
        return f'{obj.groupsubject.subjects}'
    get_subject_name.short_description = 'Дисциплина'

    def get_student_semester(self, obj):
        return f'{obj.students.semester}'
    get_student_semester.short_description = 'Семестр'

########################################################################################################################


@admin.register(Basis)
class BasisAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    ordering = ['id']

########################################################################################################################


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('id', 'semester')
    ordering = ['semester']
