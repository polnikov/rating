from django.urls import path

from students import views


app_name = 'students'

urlpatterns = [
    # Students
    path('', views.StudentListView.as_view(), name='students'),
    path('add/', views.StudentCreateView.as_view(), name='add'),
    path('<int:pk>/', views.StudentDetailView.as_view(), name='detail'),
    path('<int:pk>/delete/', views.StudentDeleteView.as_view(), name='delete'),
    path('<int:pk>/update/', views.StudentUpdateView.as_view(), name='update'),

    # Students actions
    path('import/', views.import_students, name='import'),
    path('transfer/', views.transfer_students, name='transfer'),

    # Students debts
    path('debts/', views.StudentsDebtsListView.as_view(), name='debts'),
    path('debts/debts-to-excel/', views.download_excel_data, name='debts-to-excel'),

    # Students rating
    path('rating/', views.StudentRatingTableView.as_view(), name='rating'),
    path('json/rating/', views.StudentRatingApiView.as_view(), name='students_rating'),

    # Students money
    path('money/', views.StudentsMoneyListView.as_view(), name='money'),

    # Searching
    path('search/', views.search_results, name='search'),

    # Results
    path('results/add/', views.ResultCreateView.as_view(), name='result_add'),
    path('results/delete/<int:pk>/', views.ResultDeleteView.as_view(), name='result_delete'),
    path('results/update/<int:pk>/', views.ResultUpdateView.as_view(), name='result_update'),
]
