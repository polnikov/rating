from api import views

from django.urls import include, path

from rest_framework import routers


app_name = 'api'

router = routers.SimpleRouter()
router.register('students', views.StudentViewSet)
router.register('money', views.StudentMoneyList)
router.register('results', views.ResultViewSet)
router.register('groups', views.GroupsViewSet)
router.register('cathedras', views.CathedraViewSet)
router.register('faculties', views.FacultyViewSet)
router.register('subjects', views.SubjectViewSet)
router.register('groupsubjects', views.GroupSubjectViewSet)
router.register('semesters', views.SemesterViewSet)

urlpatterns = [
    path('v1/', include(router.urls)),
    # Students history
    path('v1/students/history/', views.StudentLogList.as_view()),
    # Students money
    # path('v1/students/money/', views.StudentMoneyList.as_view()),
    # Subjects history
    path('v1/subjects/history/', views.SubjectLogList.as_view()),
]

