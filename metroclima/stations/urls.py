from django.urls import path

from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('map/', views.show_map, name='stations_map'),
    path('', views.StationListView.as_view(), name='stations_list'),
    path('<slug:slug>/', views.StationDetailView.as_view(), name='stations_detail'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
