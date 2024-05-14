import os.path

from django.shortcuts import render
import folium
from django.views.generic import ListView, DetailView
import pandas as pd
from os.path import dirname, join

from .models import Station
from .mygraphs import station_graphs


def show_map(request):
    figure = folium.Figure()
    m = folium.Map(
        location=[-23.52, -46.633],
        zoom_start=11,
        tiles='OpenStreetMap'
    )
    stations = Station.objects.all()
    for station in stations:

        info = f"""
        <h5><b>{station.name} Station</b></h5>
        <b>Latitude:</b> {station.latitude}
        <br><b>Longitude:</b> {station.longitude}
        <br><b>Elevation:</b> {station.elevation} m
        <br><a href="/stations/{station.slug}" style="text-decoration:none" target="_blank">more info</a>
        """
        text = folium.Html(info, script=True)
        info = folium.Popup(text, max_width=200, min_width=200)

        folium.Marker(
            location=[station.latitude, station.longitude],
            popup=info,
            icon=folium.Icon(color='darkblue', icon='circle', prefix='fa')
        ).add_to(m)

    m.add_to(figure)
    figure.render()
    return render(request, "stations/stations_map.html", {"map": figure})


class StationListView(ListView):
    model = Station
    template_name = 'stations/stations_list.html'
    context_object_name = 'stations'


# class StationDetailView(DetailView):
#     model = Station
#     template_name = 'stations/stations_detail.html'
#     context_object_name = 'station'


def station_detail(request, slug):
    station = Station.objects.get(slug=slug)
    if os.path.exists(join(dirname(__file__), f'../static/data/{slug}.txt')):
        df = pd.read_csv(join(dirname(__file__), f'../static/data/{slug}.txt'))
        df['DATE_TIME'] = pd.to_datetime(df.DATE_TIME)
        script, div = station_graphs(df)
        context = {'station': station, 'script': script, 'div': div}
        return render(request, 'stations/stations_detail.html', context)
    else:
        df = pd.DataFrame({'A': []})
        script, div = station_graphs(df)
        context = {'station': station}
        context = {'station': station, 'script': script, 'div': div}
        return render(request, 'stations/stations_detail.html', context)
