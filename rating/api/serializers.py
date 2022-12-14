from collections import Counter

from rest_framework import serializers

from django.contrib.auth.models import User
from django.db.models import Q, F

from students.models import Basis, Result, Semester, Student, StudentLog
from subjects.models import Subject, SubjectLog, GroupSubject, Cathedra, Faculty
from groups.models import Group


# Students
########################################################################################################################
class StudentSerializer(serializers.ModelSerializer):
    group = serializers.SlugRelatedField(slug_field='name', queryset=Group.objects)
    basis = serializers.SlugRelatedField(slug_field='name', queryset=Basis.objects)
    history = serializers.SerializerMethodField(read_only=True)
    results = serializers.SerializerMethodField(read_only=True)
    rating = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Student
        fields = (
            'student_id',
            'fullname',
            'last_name',
            'first_name',
            'second_name',
            'status',
            'group',
            'semester',
            'basis',
            'citizenship',
            'level',
            'start_date',
            'money',
            'comment',
            'tag',
            'is_archived',
            'results',
            'rating',
            'history',
        )

    def get_history(self, obj):
        student_id = obj.student_id
        history = StudentLog.objects.select_related('user').filter(record_id=student_id).annotate(
            author=F('user_id__username'),
        ).values(
            'id',
            'author',
            'field',
            'old_value',
            'new_value',
        )
        return history

    def get_results(self, obj):
        student_id = obj.student_id
        results = Result.objects.select_related().filter(students=student_id).annotate(
            group=F('groupsubject_id__groups__name'),
            semester=F('groupsubject_id__subjects__semester'),
            subject=F('groupsubject_id__subjects__name'),
            form_control=F('groupsubject_id__subjects__form_control'),
        ).values(
            'id',
            'group',
            'semester',
            'subject',
            'form_control',
            'mark',
            'tag',
            'is_archived',
        )
        return results

    def get_rating(self, obj):
        student_id = obj.student_id
        student = Student.objects.select_related('group', 'semester', 'basis').get(student_id__exact=student_id)
        
        # ?????? ???????????? ????????????????
        marks = Result.objects.select_related().filter(
            students=student.student_id).filter(
            ~Q(groupsubject__subjects__form_control__exact='??????????'))
        # ?????? ???????????????????? ?????? ?????????????? ?????????????????????? (????????????), ???????????????? ????????????
        atts = GroupSubject.objects.select_related('subjects').filter(
            groups=student.group,
            is_archived=False
        ).filter(~Q(subjects__form_control__exact='??????????'))

        # ???????????????????? ???????????????? ?????????? ???? ?????????????????? ?? ????????????????????
        rating_by_semester_bac = {
            1: 0,
            2: 0,
            3: 0,
            4: 0,
            5: 0,
            6: 0,
            7: 0,
            8: 0,
        }
        rating_by_semester_mag = {
            1: 0,
            2: 0,
            3: 0,
            4: 0,
        }
        all_num_marks = []
        all_marks = []
        if student.level == '??????????????????????':
            semesters = range(1, 9)
            rating_by_semester = rating_by_semester_bac
        elif student.level == '????????????????????????':
            semesters = range(1, 5)
            rating_by_semester = rating_by_semester_mag

        for i in semesters:
            # ?????? ???????????? ???? ??????????????
            sem_marks_all = marks.select_related('subjects').filter(
                groupsubject__subjects__semester__semester=i
            ).values('mark')
            # ?????????? ???????????? ?????????????????? ???????????? ?? ?????????????????? <????> ?? <2>
            sem_marks = list(filter(lambda x: x not in ['????', '2'], [i['mark'][-1] for i in sem_marks_all]))
            all_marks += sem_marks
            # ???????????????????? ???????????????????? ?? ???????????????? ?? ????????????????
            num_atts = atts.filter(subjects__semester=i).count()
            all_num_marks.append(num_atts)
            # ???????????????????? ???????????? ???? ???????????? <3 | 4 | 5>
            count_marks = dict(Counter(sem_marks))
            # ???????????????????? ?????????????? ???????? ???? ??????????????
            try:
                sem_rating = round(sum([int(k)*v for k, v in count_marks.items()]) / num_atts, 2)
            except ZeroDivisionError:
                sem_rating = 0
            rating_by_semester[i] = sem_rating

        # ???????????????????? ?????????????????? ?????????????? ????????
        try:
            rating = round(sum(list(map(int, (all_marks)))) / sum(all_num_marks), 2)
        except ZeroDivisionError:
            rating = 0

        context = {
            'rating': rating,
            'rating_by_semester': rating_by_semester
        }
        return context


class StudentLogSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username', queryset=User.objects)

    class Meta:
        model = StudentLog
        fields = ('record_id', 'user', 'field', 'old_value', 'new_value', 'timestamp',)


# ! TODO: API for trans students
# ! TODO: API for students debts






class StudentMoneySerializer(serializers.ModelSerializer):
    group = serializers.SlugRelatedField(slug_field='name', queryset=Group.objects)
    basis = serializers.SlugRelatedField(slug_field='name', queryset=Basis.objects)

    class Meta:
        model = Student
        fields = ('student_id', 'fullname', 'group', 'semester', 'money', 'basis',)





# GroupSubjects
########################################################################################################################
class GroupSubjectSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(slug_field='name', queryset=Group.objects)
    subjects = serializers.SlugRelatedField(slug_field='name', queryset=Subject.objects)

    class Meta:
        model = GroupSubject
        fields = ('id', 'groups', 'subjects', 'teacher', 'att_date')


# Results
########################################################################################################################
class ResultSerializer(serializers.ModelSerializer):
    students = serializers.SlugRelatedField(slug_field='fullname', queryset=Student.objects)
    groupsubject = GroupSubjectSerializer()


    class Meta:
        model = Result
        fields = ('id', 'students', 'groupsubject', 'mark', 'tag', 'is_archived',)


# Groups
########################################################################################################################
class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = ('id', 'name', 'direction', 'profile', 'level', 'code', 'is_archived',)


# Subjects
########################################################################################################################
class SubjectSerializer(serializers.ModelSerializer):
    cathedra = serializers.SlugRelatedField(slug_field='name', queryset=Cathedra.objects)
    history = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Subject
        fields = ('id', 'name', 'form_control', 'semester', 'cathedra', 'zet', 'comment', 'is_archived', 'history',)

    def get_history(self, obj):
        subject_id = obj.id
        history = SubjectLog.objects.select_related('user').filter(record_id=subject_id).annotate(
            author=F('user_id__username'),
        ).values(
            'id',
            'author',
            'field',
            'old_value',
            'new_value',
        )
        return history


class SubjectLogSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username', queryset=User.objects)

    class Meta:
        model = SubjectLog
        fields = ('id', 'record_id', 'user', 'field', 'old_value', 'new_value', 'timestamp',)


# Cathedras
########################################################################################################################
class CathedraSerializer(serializers.ModelSerializer):
    faculty = serializers.SlugRelatedField(slug_field='name', queryset=Faculty.objects)

    class Meta:
        model = Cathedra
        fields = ('id', 'name', 'short_name', 'faculty',)


# Faculties
########################################################################################################################
class FacultySerializer(serializers.ModelSerializer):

    class Meta:
        model = Faculty
        fields = ('id', 'name', 'short_name',)


# Semesters
########################################################################################################################
class SemesterSerializer(serializers.ModelSerializer):

    class Meta:
        model = Semester
        fields = ('id', 'semester',)
