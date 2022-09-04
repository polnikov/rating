from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic import View

from groups.models import Group
from students.models import Result, Student
from subjects.models import GroupSubject, Subject


class ArchiveApiView(LoginRequiredMixin, View):
    def get(self, request):
        qs_filter = {'is_archived': True}
        students = Student.objects.select_related().filter(**qs_filter)
        results = Result.objects.select_related().filter(**qs_filter)
        subjects = Subject.objects.select_related().filter(**qs_filter)
        group_subjects = GroupSubject.objects.select_related().filter(**qs_filter)
        groups = Group.objects.select_related().filter(**qs_filter)

        students_serialized_data = []
        for item in students:
            students_serialized_data.append({
                'id': item.student_id,
                'fullname': item.fullname,
                'group': item.group.name,
                'semester': item.semester.semester,
                'status': item.status,
                'tag': item.tag,
                'comment': item.comment,
            })

        results_serialized_data = []
        for item in results:
            results_serialized_data.append({
                'id': item.id,
                'student': item.students.fullname,
                'group': item.groupsubject.groups.name,
                'semester': item.groupsubject.subjects.semester.semester,
                'subject': item.groupsubject.subjects.name,
                'form control': item.groupsubject.subjects.form_control,
                'teacher': item.groupsubject.subjects.empty_teacher,
                'att date': item.groupsubject.subjects.empty_att_date,
                'marks': item.mark,
                'tag': item.tag,
            })

        subjects_serialized_data = []
        for item in subjects:
            subjects_serialized_data.append({
                'id': item.id,
                'name': item.name,
                'form control': item.form_control,
                'semester': item.semester.semester,
                'teacher': item.empty_teacher,
                'att date': item.empty_att_date,
            })

        group_subjects_serialized_data = []
        for item in group_subjects:
            group_subjects_serialized_data.append({
                'id': item.id,
                'name': item.subjects.name,
                'form control': item.subjects.form_control,
                'groups': item.groups.name,
                'semester': item.subjects.semester.semester,
                'att date': item.subjects.empty_att_date,
            })

        groups_serialized_data = []
        for item in groups:
            groups_serialized_data.append({
                'id': item.id,
                'name': item.name,
                'direction': item.direction,
                'profile': item.profile,
                'level': item.level,
                'code': item.code,
            })

        data = {
            'students': students_serialized_data,
            'results': results_serialized_data,
            'subjects': subjects_serialized_data,
            'group_subjects': group_subjects_serialized_data,
            'groups': groups_serialized_data,
        }

        return JsonResponse(data)
