from django.urls import path

from groups import views


app_name = 'groups'

urlpatterns = [
    path('', views.GroupListView.as_view(), name='groups'),
    path('add/', views.GroupCreateView.as_view(), name='add'),
    path('<int:pk>/delete/', views.GroupDeleteView.as_view(), name='delete'),
    path('<int:pk>/update/', views.GroupUpdateView.as_view(), name='update'),
    path('cards/', views.GroupCardsView.as_view(), name='cards'),
    path('cards/<str:groupname>-<int:semester>/', views.GroupDetailListView.as_view(), name='detail'),
    path('json/groupmarks/', views.GroupMarksApiView.as_view(), name='groupmarks'),
]
