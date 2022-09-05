from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import include, path
from django.views.generic.base import RedirectView

from subjects import views


urlpatterns = [
    path('admin/', admin.site.urls),
]
urlpatterns += [
    path('favicon.ico', RedirectView.as_view(url=staticfiles_storage.url('img/favicon.ico'))),
    path('accounts/', include('django.contrib.auth.urls')),
    # path('logout/', logout_page.as_view(), name='logout'),
    path('', RedirectView.as_view(url='/groups/cards')),
    path('archive/', include('archive.urls', namespace='archive')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('groups/', include('groups.urls', namespace='groups')),
    path('students/', include('students.urls', namespace='students')),
    path('subjects/', include('subjects.urls', namespace='subjects')),
    path('debug/', include('debug_toolbar.urls')),
]
