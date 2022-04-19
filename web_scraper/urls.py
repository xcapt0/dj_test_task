from django.urls import include, path

urlpatterns = [
    path('', include('scraper.urls'))
]
