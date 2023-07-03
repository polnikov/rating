from api import views

from django.urls import include, path

from rest_framework import routers


app_name = 'api'

router = routers.SimpleRouter()
router.register('students', views.StudentViewSet)              # [+]
router.register('results', views.ResultViewSet)                # [+]
router.register('groups', views.GroupsViewSet)                 # [+]
router.register('cathedras', views.CathedraViewSet)            # [+]
router.register('faculties', views.FacultyViewSet)             # [+]
router.register('subjects', views.SubjectViewSet)              # [+]
router.register('groupsubjects', views.GroupSubjectViewSet)    # [+]

urlpatterns = [
    path('v1/', include(router.urls)),
    path('v1/activestudents/', views.StudentsList.as_view()),            # [+]
    path('v1/history/students/', views.StudentLogList.as_view()),        # [+]
    path('v1/archivedstudents/', views.StudentsArchivedList.as_view()),  # [+]
    path('v1/studentresults/', views.ResultsForStudentList.as_view()),   # [+]
    path('v1/activesubjects/', views.SubjectsList.as_view()),            # [+]
    # path('v1/history/subjects/', views.SubjectLogList.as_view()),        # [-]
    path('v1/archivedsubjects/', views.SubjectsArchivedList.as_view()),  # [+]
    path('v1/archivedresults/', views.ResultsArchivedList.as_view()),    # [+]
    path('v1/subjectresults/', views.ResultsForSubjectList.as_view()),  # [+]
    path('v1/activegroupsubjects/', views.GroupSubjectsList.as_view()),  # [+]
    # path('v1/money/', views.StudentMoneyList.as_view()),                 # [-]
    # path('v1/debts/students/', views.students_debts),                    # [-]
    # path('v1/rating/', views.student_rating),  # [-]

    path('v1/resetgroupsubjects/', views.reset_groupsubjects),  # [+]

    path('v1/transfer/students/', views.transfer_students),  # [+]
    path('v1/groupmarks/', views.group_marks),               # [+]

    path('v1/import/students/', views.import_students),              # [+]
    path('v1/import/results/', views.import_results),                # [+]
    path('v1/import/cathedras/', views.import_cathedras),            # [+]
    path('v1/import/subjects/', views.import_subjects),              # [+]
    path('v1/import/groupsubjects/', views.import_groupsubjects),    # [+]
]
