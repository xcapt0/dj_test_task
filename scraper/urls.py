from django.urls import path, re_path
from django.views.static import serve
from . import views
from web_scraper import settings


urlpatterns = [
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),

    path('', views.Index.as_view(), name='index'),
    path('search', views.Scraper.as_view(), name='scraper')
]