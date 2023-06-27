from django.urls import path

from subjects import views


app_name = 'subjects'

urlpatterns = [
    path('', views.SubjectView.as_view(), name='subjects'),
    path('<int:pk>/', views.SubjectDetailView.as_view(), name='detail'),
    path('debts/', views.SubjectsDebtsListView.as_view(), name='debts'),
    path('faculties/', views.FacultyView.as_view(), name='faculties'),
    path('cathedras/', views.CathedraView.as_view(), name='cathedras'),
    path('groupsubjects/', views.GroupSubjectView.as_view(), name='groupsubjects'),
]
