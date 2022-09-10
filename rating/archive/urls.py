from archive import apiviews, views
from django.urls import path


app_name = 'archive'

urlpatterns = [
    path('', views.ArchiveDataView.as_view(), name='archive'),

    # API
    path('api/all/', apiviews.ArchiveApiView.as_view(), name='api_archive'),
]
