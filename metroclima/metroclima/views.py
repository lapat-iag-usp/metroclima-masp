from django.http import HttpResponse


def maintenance_page(request):
    html = "<html><body>We will be back soon :)</body></html>"
    return HttpResponse(html)
