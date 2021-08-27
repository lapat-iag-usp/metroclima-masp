from django.shortcuts import render
from django.views.generic import ListView

from .models import Group, Member


class MemberListView(ListView):
    context_object_name = 'members'
    template_name = 'members/members_list.html'
    # queryset = Member.objects.filter()
    queryset = Member.objects.all().order_by('name')

    def get_context_data(self, **kwargs):
        context = super(MemberListView, self).get_context_data(**kwargs)
        context['groups'] = Group.objects.all().order_by('order')
        return context
