from rest_framework import serializers

from students.models import Basis, Result, Semester, Student, StudentLog
from subjects.models import Subject, SubjectLog, GroupSubject, Cathedra, Faculty
from groups.models import Group
from django.contrib.auth.models import User


# Students
########################################################################################################################
class StudentSerializer(serializers.ModelSerializer):
    group = serializers.SlugRelatedField(slug_field='name', queryset=Group.objects)
    basis = serializers.SlugRelatedField(slug_field='name', queryset=Basis.objects)
    history = serializers.SerializerMethodField(read_only=True)
    results = serializers.SerializerMethodField(read_only=True)

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
            'history',
        )


    def get_history(self, obj):
        student_id = obj.student_id
        history = StudentLog.objects.select_related('user').filter(record_id=student_id).values(
            'id',
            'user_id__username',
            'field',
            'old_value',
            'new_value',
        )
        return history


    def get_results(self, obj):
        student_id = obj.student_id
        results = Result.objects.select_related().filter(students=student_id).values(
            'id',
            'groupsubject_id__groups__name',
            'groupsubject_id__subjects__semester',
            'groupsubject_id__subjects__name',
            'groupsubject_id__subjects__form_control',
            'mark',
            'tag',
            'is_archived',
        )
        return results


class StudentLogSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username', queryset=User.objects)

    class Meta:
        model = StudentLog
        fields = ('record_id', 'user', 'field', 'old_value', 'new_value', 'timestamp',)


# ! TODO: API for calc ranking
# ! TODO: API for trans students
# ! TODO: API for students debts


class StudentMoneySerializer(serializers.ModelSerializer):
    group = serializers.SlugRelatedField(slug_field='name', queryset=Group.objects)
    basis = serializers.SlugRelatedField(slug_field='name', queryset=Basis.objects)

    class Meta:
        model = Student
        fields = (
            'student_id',
            'fullname',
            'group',
            'semester',
            'money',
            'basis',
        )


# GroupSubjects
########################################################################################################################
class GroupSubjectSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(slug_field='name', queryset=Group.objects)
    subjects = serializers.SlugRelatedField(slug_field='name', queryset=Subject.objects)

    class Meta:
        model = GroupSubject
        fields = ('id', 'groups', 'subjects',)


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
        fields = (
            'id',
            'name',
            'form_control',
            'semester',
            'cathedra',
            'teacher',
            'zet',
            'att_date',
            'comment',
            'is_archived',
            'history',
        )

    def get_history(self, obj):
        subject_id = obj.id
        history = SubjectLog.objects.select_related('user').filter(record_id=subject_id).values(
            'id',
            'user_id__username',
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
