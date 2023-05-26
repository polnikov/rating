from django.urls import path

from groups import views


app_name = 'groups'

urlpatterns = [
    path('', views.GroupView.as_view(), name='groups'),
    path('cards/', views.GroupCardsView.as_view(), name='cards'),
    path('cards/<str:groupname>-<int:semester>/', views.GroupDetailListView.as_view(), name='detail'),
]
