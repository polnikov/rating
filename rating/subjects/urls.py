from django.urls import path

from subjects import views


app_name = 'subjects'

urlpatterns = [
    # Subjects
    path('', views.SubjectListView.as_view(), name='subjects'),
    path('add/', views.SubjectCreateView.as_view(), name='add'),
    path('<int:pk>/', views.SubjectDetailView.as_view(), name='detail'),
    path('<int:pk>/delete/', views.SubjectDeleteView.as_view(), name='delete'),
    path('<int:pk>/update/', views.SubjectUpdateView.as_view(), name='update'),

    # Subjects actions
    path('import/', views.import_subjects, name='subjects_import'),

    # Subjects debts
    path('debts/', views.SubjectsDebtsListView.as_view(), name='debts'),

    path('json/', views.subjects_json, name='subjects_json'),

    # Faculties
    path('faculties/', views.FacultyListView.as_view(), name='faculties'),
    path('faculties/add/', views.FacultyCreateView.as_view(), name='faculty_add'),
    path('faculties/<int:pk>/delete/', views.FacultyDeleteView.as_view(), name='faculty_delete'),
    path('faculties/<int:pk>/update/', views.FacultyUpdateView.as_view(), name='faculty_update'),

    # Cathedras
    path('cathedras/', views.CathedraListView.as_view(), name='cathedras'),
    path('cathedras/add/', views.CathedraCreateView.as_view(), name='cathedra_add'),
    path('cathedras/<int:pk>/delete/', views.CathedraDeleteView.as_view(), name='cathedra_delete'),
    path('cathedras/<int:pk>/update/', views.CathedraUpdateView.as_view(), name='cathedra_update'),

    # Cathedras actions
    path('cathedras/import/', views.import_cathedras, name='cathedras_import'),

    # GroupSubject
    path('groupsubjects/', views.GroupSubjectListView.as_view(), name='groupsubjects'),
    path('groupsubjects/add/', views.GroupSubjectCreateView.as_view(), name='groupsubject_add'),
    path('groupsubjects/<int:pk>/delete/', views.GroupSubjectDeleteView.as_view(), name='groupsubject_delete'),
    path('groupsubjects/<int:pk>/update/', views.GroupSubjectUpdateView.as_view(), name='groupsubject_update'),
    path('groupsubjects/import/', views.import_groupsubjects, name='groupsubjects_import'),
]
