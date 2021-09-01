

def stations(request):
    from stations.models import Station
    return {'stations': Station.objects.all().order_by('name')}


def campaigns(request):
    from .models import Campaign
    return {'campaigns': Campaign.objects.all().order_by('name')}
