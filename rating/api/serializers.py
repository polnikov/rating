from collections import Counter

from rest_framework import serializers

from django.contrib.auth.models import User
from django.db.models import Q, F

from students.models import Basis, Result, Semester, Student, StudentLog
from subjects.models import Subject, SubjectLog, GroupSubject, Cathedra, Faculty
from groups.models import Group


# Groups
class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = ('id', 'name', 'direction', 'profile', 'level', 'code', 'is_archived')


# Basis
class BasisSerializer(serializers.ModelSerializer):

    class Meta:
        model = Basis
        fields = ('id', 'name')


# Students
class StudentSerializer(serializers.ModelSerializer):
    group = GroupSerializer()
    basis = BasisSerializer()
    history = serializers.SerializerMethodField(read_only=True)
    results = serializers.SerializerMethodField(read_only=True)
    rating = serializers.SerializerMethodField(read_only=True)
    depth = 1

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
        
        # все оценки студента
        marks = Result.objects.select_related().filter(
            students=student.student_id).filter(
            ~Q(groupsubject__subjects__form_control__exact='Зачет'))
        # все аттестации для данного направления (группы), исключая зачеты
        atts = GroupSubject.active_objects.select_related('subjects').filter(
            groups=student.group,
        ).filter(~Q(subjects__form_control__exact='Зачет'))

        # вычисление среднего балла по семестрам и суммарного
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
        if student.level == 'Бакалавриат':
            semesters = range(1, 9)
            rating_by_semester = rating_by_semester_bac
        elif student.level == 'Магистратура':
            semesters = range(1, 5)
            rating_by_semester = rating_by_semester_mag

        for i in semesters:
            # все оценки за семестр
            sem_marks_all = marks.select_related('subjects').filter(
                groupsubject__subjects__semester__semester=i
            ).values('mark')
            # берем только последнюю оценку и исключаем <ня> и <2>
            sem_marks = list(filter(lambda x: x not in ['ня', '2'], [i['mark'][-1] for i in sem_marks_all]))
            all_marks += sem_marks
            # количество аттестаций с оценками в семестре
            num_atts = atts.filter(subjects__semester=i).count()
            all_num_marks.append(num_atts)
            # количество каждой из оценок <3 | 4 | 5>
            count_marks = dict(Counter(sem_marks))
            # определяем средний балл за семестр
            try:
                sem_rating = round(sum([int(k)*v for k, v in count_marks.items()]) / num_atts, 2)
            except ZeroDivisionError:
                sem_rating = 0
            rating_by_semester[i] = sem_rating

        # определяем суммарный средний балл
        try:
            rating = round(sum(list(map(int, (all_marks)))) / sum(all_num_marks), 2)
        except ZeroDivisionError:
            rating = 0

        context = {
            'rating': rating,
            'rating_by_semester': rating_by_semester
        }
        return context


class StudentsListSerializer(serializers.ModelSerializer):
    group = serializers.SlugRelatedField(slug_field='name', queryset=Group.objects)

    class Meta:
        model = Student
        fields = ('student_id', 'fullname', 'group', 'semester', 'level', 'citizenship', 'comment', 'is_ill', 'tag', 'status')


class StudentLogSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='last_name', queryset=User.objects)
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = StudentLog
        fields = ('record_id', 'user', 'field', 'old_value', 'new_value', 'timestamp', 'fullname')


    def get_fullname(self, obj):
        student_id = obj.record_id
        if Student.objects.filter(student_id=student_id).exists():
            student = Student.objects.get(student_id=student_id)
            return student.fullname
        else:
            return False


class StudentMoneySerializer(serializers.ModelSerializer):
    group = serializers.SlugRelatedField(slug_field='name', queryset=Group.objects)
    basis = serializers.SlugRelatedField(slug_field='name', queryset=Basis.objects)

    class Meta:
        model = Student
        fields = ('student_id', 'fullname', 'group', 'semester', 'money', 'basis')


# GroupSubjects
class SubjectsForGroupSubjectsListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subject
        fields = ('id', 'name', 'form_control', 'semester')


class GroupsForGroupSubjectsListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = ('id', 'name')


class GroupSubjectsListSerializer(serializers.ModelSerializer):
    groups = GroupsForGroupSubjectsListSerializer()
    subjects = SubjectsForGroupSubjectsListSerializer()
    semester = serializers.SerializerMethodField()
    cathedra = serializers.SerializerMethodField()

    class Meta:
        model = GroupSubject
        fields = ('id', 'groups', 'subjects', 'semester', 'teacher', 'att_date', 'cathedra', 'comment', 'is_archived')

    def get_semester(self, obj):
        semester = obj.subjects.semester.semester
        return semester

    def get_cathedra(self, obj):
        if obj.subjects.cathedra:
            return obj.subjects.cathedra.short_name
        else:
            return False


class GroupSubjectSerializer(serializers.ModelSerializer):
    groups = GroupsForGroupSubjectsListSerializer()
    subjects = SubjectsForGroupSubjectsListSerializer()
    cathedra = serializers.SerializerMethodField()

    class Meta:
        model = GroupSubject
        fields = ('id', 'groups', 'subjects', 'teacher', 'att_date', 'comment', 'cathedra', 'is_archived')

    def get_cathedra(self, obj):
        if obj.subjects.cathedra:
            return obj.subjects.cathedra.short_name
        else:
            return False


# Results
class StudentsForResultsArchivedSerializer(serializers.ModelSerializer):

    class Meta:
        model = Student
        fields = ('student_id', 'fullname')


class ResultSerializer(serializers.ModelSerializer):
    students = StudentsForResultsArchivedSerializer()
    groupsubject = GroupSubjectSerializer()

    class Meta:
        model = Result
        fields = ('id', 'students', 'groupsubject', 'mark', 'tag', 'is_archived')


class ResultArchivedSerializer(serializers.ModelSerializer):
    students = StudentsForResultsArchivedSerializer()
    groupsubject = GroupSubjectsListSerializer()

    class Meta:
        model = Result
        fields = ('id', 'students', 'groupsubject', 'mark', 'tag')


# Cathedras
class CathedraSerializer(serializers.ModelSerializer):

    class Meta:
        model = Cathedra
        fields = ('id', 'name', 'short_name', 'faculty')
        depth = 1


# Subjects
class SubjectsListSerializer(serializers.ModelSerializer):
    cathedra = serializers.SlugRelatedField(slug_field='short_name', queryset=Cathedra.objects)
    semester = serializers.SlugRelatedField(slug_field='semester', queryset=Semester.objects)

    class Meta:
        model = Subject
        fields = ('id', 'name', 'form_control', 'semester', 'cathedra', 'comment')


class SubjectSerializer(serializers.ModelSerializer):
    cathedra = CathedraSerializer()
    history = serializers.SerializerMethodField(read_only=True)
    groups = serializers.SerializerMethodField()


    class Meta:
        model = Subject
        fields = (
            'id',
            'name',
            'form_control',
            'semester',
            'cathedra',
            'zet',
            'comment',
            'is_archived',
            'history',
            'groups',
        )
        depth = 1

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

    def get_groups(self, obj):
        subject_id = obj.id
        groups_data = GroupSubject.objects.filter(subjects=subject_id).order_by('subjects__group__name')
        groups = []
        for group in groups_data:
            groups.append(f'{group.groups}-{group.subjects.semester.semester}')
        return groups


class SubjectLogSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username', queryset=User.objects)

    class Meta:
        model = SubjectLog
        fields = ('id', 'record_id', 'user', 'field', 'old_value', 'new_value', 'timestamp')


# Faculties
class FacultySerializer(serializers.ModelSerializer):

    class Meta:
        model = Faculty
        fields = ('id', 'name', 'short_name')


# Semesters
class SemesterSerializer(serializers.ModelSerializer):

    class Meta:
        model = Semester
        fields = ('id', 'semester')
