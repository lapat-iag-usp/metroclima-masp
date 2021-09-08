from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    path('', login_required(views.DashboardView.as_view()), name='ds_home'),
    path('stations/<slug:slug>/', login_required(views.DashboardStationsView.as_view()), name='ds_stations'),
    path('raw/<slug:slug>/', views.graphs_raw, name='ds_raw'),
    path('raw-24h/<slug:slug>/', views.graphs_raw_24h, name='ds_raw_24h'),
]
