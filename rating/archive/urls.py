from archive import views

from django.urls import path


app_name = 'archive'

urlpatterns = [
    path('', views.ArchiveDataView.as_view(), name='archive'),
    path('help', views.HelpPageView.as_view(), name='help'),
]
