from django.urls import path

from . import views

urlpatterns = [
    path('', views.MemberListView.as_view(), name='members_list'),

]
