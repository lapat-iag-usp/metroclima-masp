from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, DetailView
from django.shortcuts import render
import glob
import dask.dataframe as dd
import pandas as pd

from stations.models import Station
from .models import Campaign
from .mygraphs import bokeh_raw
from .forms import DataRawFormFunction


class DashboardView(TemplateView):
    template_name = 'dashboard/ds_home.html'


class DashboardStationsView(DetailView):
    model = Station
    template_name = 'dashboard/ds_stations.html'
    context_object_name = 'station'


@login_required
def graphs_raw(request, slug):
    campaign = Campaign.objects.get(slug=slug)

    # form choices
    if campaign.raw_data_path:
        path = campaign.raw_data_path
        filenames = [filename for filename in glob.iglob(
            path + '**/*.dat', recursive=True)]
        if filenames:
            filenames.sort(reverse=True)
            file_choices = list(
                zip(filenames,
                    [filename.split('/')[-1] for filename in filenames]))

            # initial values
            files_name = filenames[0]
            initial_data = {'files_name': files_name}

            # form
            raw_data_form = DataRawFormFunction(file_choices)
            form = raw_data_form(request.POST or None, initial=initial_data)
            if form.is_valid():
                files_name = request.POST.get('files_name')
                idx = filenames.index(files_name)
                if '_prev' in request.POST:
                    if idx + 1 > (len(filenames) - 1):
                        files_name = filenames[idx + 1 - (len(filenames))]
                    else:
                        files_name = filenames[idx + 1]
                    form = raw_data_form(initial={'files_name': files_name})
                elif '_next' in request.POST:
                    files_name = filenames[idx - 1]
                    form = raw_data_form(initial={'files_name': files_name})

            # dataframe
            usecols = campaign.raw_var_list.split(',')
            dtype = campaign.raw_dtypes.split(',')
            dtype = dict(zip(usecols, dtype))
            df = dd.read_csv(files_name,
                             sep=r'\s+',
                             usecols=usecols,
                             dtype=dtype,
                             )
            df = df.compute()
            df['DATE_TIME'] = pd.to_datetime(df['DATE'] + ' ' + df['TIME'])
            df = df.drop(['DATE', 'TIME'], axis=1)

            script, div = bokeh_raw(df)
            context = {'campaign': campaign,
                       'form': form,
                       'script': script, 'div': div}
            return render(request, 'dashboard/ds_raw.html', context)

        else:
            # form
            raw_data_form = DataRawFormFunction([('', 'no data available')])
            form = raw_data_form(request.POST or None)
            context = {'campaign': campaign, 'form': form}
            return render(request, 'dashboard/ds_raw.html', context)

    else:
        context = {'campaign': campaign}
        return render(request, 'dashboard/ds_raw.html', context)
