from archive import apiviews, views
from django.urls import path


app_name = 'archive'

urlpatterns = [
    path('students/', views.ArchiveStudentsView.as_view(), name='students'),
    path('marks/', views.ArchiveMarksView.as_view(), name='marks'),
    path('subjects/', views.ArchiveSubjectsView.as_view(), name='subjects'),
    path('groupsubjects/', views.ArchiveGroupsubjectsView.as_view(), name='groupsubjects'),
    path('groups/', views.ArchiveGroupsView.as_view(), name='groups'),

    # API
    path('api/all', apiviews.ArchiveApiView.as_view(), name='api_archive'),
]
