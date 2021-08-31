

def stations(request):
    from stations.models import Station
    return {'stations': Station.objects.all()}
