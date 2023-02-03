from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import include, path
from django.views.generic.base import RedirectView
from django.shortcuts import render


urlpatterns = [
    path('admin/', admin.site.urls),
]
urlpatterns += [
    path('favicon.ico', RedirectView.as_view(url=staticfiles_storage.url('img/favicon.ico'))),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', RedirectView.as_view(url='/groups/cards')),
    path('archive/', include('archive.urls', namespace='archive')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('groups/', include('groups.urls', namespace='groups')),
    path('students/', include('students.urls', namespace='students')),
    path('subjects/', include('subjects.urls', namespace='subjects')),
    path('__debug__/', include('debug_toolbar.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('api/', include('api.urls', namespace='api')),
]


def custom_404(request, exception=None):
    return render(request, '404.html', status=404)


handler404 = custom_404
