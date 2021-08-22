from django.http import HttpResponse
from django.views.generic import TemplateView


def maintenance_page(request):
    html = "<html><body>We will be back soon :)</body></html>"
    return HttpResponse(html)


class HomeView(TemplateView):
    template_name = 'home.html'
