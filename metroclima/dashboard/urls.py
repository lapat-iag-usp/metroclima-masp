from django.urls import path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    path('', login_required(views.DashboardView.as_view()), name='ds_home'),
    path('upload', login_required(views.DashboardUploadView.as_view()), name='ds_upload'),
    path('download', login_required(views.DashboardDownloadView.as_view()), name='ds_download'),
    path('download/<slug:slug>/files/', views.DashboardDownloadFilesView.as_view(), name='ds_download_files'),
    path('download/<slug:slug>/files/all/', views.download_all_files, name='download_all_files'),
    path('file_transfer', views.file_transfer, name='ds_file_transfer'),
    path('folder_transfer', views.folder_transfer, name='ds_folder_transfer'),
    path('data_overview', views.data_overview, name='ds_data_overview'),
    path('tutorials', views.tutorials, name='ds_tutorials'),
    path('stations/<slug:slug>/', login_required(views.DashboardStationsView.as_view()), name='ds_stations'),
    path('raw/<slug:slug>/', views.graphs_raw, name='ds_raw'),
    path('raw-24h/<slug:slug>/', views.graphs_raw_24h, name='ds_raw_24h'),
    path('level-0/<slug:slug>/', views.graphs_level_0, name='ds_level_0'),
    path('mobile/<slug:slug>/', login_required(views.DashboardMobileView.as_view()), name='ds_mobile'),
    path('mobile/raw-24h/<slug:slug>/', views.graphs_raw_24h_mobile, name='ds_raw_24h_mobile'),
    path('export/<slug:slug>/', views.export_logbook_csv, name='export_logbook_csv'),
]
