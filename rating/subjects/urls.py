from django.urls import path

from subjects import views


app_name = 'subjects'

urlpatterns = [
    # Subjects
    path('', views.SubjectView.as_view(), name='subjects'),
    path('<int:pk>/', views.SubjectDetailView.as_view(), name='detail'),

    # Subjects debts
    path('debts/', views.SubjectsDebtsListView.as_view(), name='debts'),

    # Faculties
    path('faculties/', views.FacultyView.as_view(), name='faculties'),

    # Cathedras
    path('cathedras/', views.CathedraView.as_view(), name='cathedras'),

    # GroupSubject
    path('groupsubjects/', views.GroupSubjectListView.as_view(), name='groupsubjects'),
    path('groupsubjects/add/', views.GroupSubjectCreateView.as_view(), name='groupsubject_add'),
    path('groupsubjects/<int:pk>/delete/', views.GroupSubjectDeleteView.as_view(), name='groupsubject_delete'),
    path('groupsubjects/<int:pk>/update/', views.GroupSubjectUpdateView.as_view(), name='groupsubject_update'),
    path('groupsubjects/import/', views.import_groupsubjects, name='groupsubjects_import'),
]
