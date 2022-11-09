from api import serializers

from groups.models import Group

from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from students.models import Result, Semester, Student, StudentLog

from subjects.models import Cathedra, Faculty, GroupSubject, Subject, SubjectLog


# Students
########################################################################################################################
class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = serializers.StudentSerializer


class StudentLogList(generics.ListAPIView):
    queryset = StudentLog.objects.all()
    serializer_class = serializers.StudentLogSerializer


class StudentMoneyList(viewsets.ReadOnlyModelViewSet):
    queryset = Student.objects.select_related('basis', 'group', 'semester').filter(is_archived=False)
    serializer_class = serializers.StudentMoneySerializer


# ! TODO: API for calc ranking
# ! TODO: API for trans students
# ! TODO: API for students debts


# Results
########################################################################################################################
class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.all()
    serializer_class = serializers.ResultSerializer


# Groups
########################################################################################################################
class GroupsViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer


# Faculties
########################################################################################################################
class FacultyViewSet(viewsets.ModelViewSet):
    queryset = Faculty.objects.all()
    serializer_class = serializers.FacultySerializer


# Cathedras
########################################################################################################################
class CathedraViewSet(viewsets.ModelViewSet):
    queryset = Cathedra.objects.all()
    serializer_class = serializers.CathedraSerializer


# Subjects
########################################################################################################################
class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = serializers.SubjectSerializer


class SubjectLogList(generics.ListAPIView):
    queryset = SubjectLog.objects.all()
    serializer_class = serializers.SubjectLogSerializer


# GroupSubjects
########################################################################################################################
class GroupSubjectViewSet(viewsets.ModelViewSet):
    queryset = GroupSubject.objects.all()
    serializer_class = serializers.GroupSubjectSerializer


# Semesters
########################################################################################################################
class SemesterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Semester.objects.all()
    serializer_class = serializers.SemesterSerializer
