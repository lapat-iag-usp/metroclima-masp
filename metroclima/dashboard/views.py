from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, DetailView
from django.shortcuts import render
from django.http import HttpResponse
import glob
import dask.dataframe as dd
import pandas as pd
from datetime import datetime, timedelta
import zipfile

from stations.models import Station, Instrument
from .models import Campaign
from .mygraphs import bokeh_raw, bokeh_raw_mobile
from .forms import DataRawFormFunction, DataRaw24hFormFunction


class DashboardView(TemplateView):
    template_name = 'dashboard/ds_home.html'


class DashboardStationsView(DetailView):
    model = Station
    template_name = 'dashboard/ds_stations.html'
    context_object_name = 'station'


class DashboardMobileView(DetailView):
    model = Instrument
    template_name = 'dashboard/ds_mobile.html'
    context_object_name = 'instrument'


@login_required
def graphs_raw(request, slug):
    my_download = 0
    campaign = Campaign.objects.get(slug=slug)

    # form choices
    if campaign.raw_data_path:
        path = campaign.raw_data_path
        filenames = [filename for filename in glob.iglob(
            path + '**/*.dat', recursive=True)]
        if filenames:
            filenames.sort(reverse=True)
            # ignoring last file as a temporary solution to broken line files
            # using "skipfooter" compromises the time of processing
            filenames = filenames[1:]
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
                elif '_download' in request.POST:
                    my_download = 1

            # dataframe
            usecols = campaign.raw_var_list.split(',')
            dtype = campaign.raw_dtypes.split(',')
            dtype = dict(zip(usecols, dtype))
            df = dd.read_csv(files_name,
                             sep=r'\s+',
                             usecols=usecols,
                             dtype=dtype,
                             engine='c',
                             )
            df = df.compute()
            df['DATE_TIME'] = pd.to_datetime(df['DATE'] + ' ' + df['TIME'])
            df = df.drop(['DATE', 'TIME'], axis=1)
            df = df[['DATE_TIME'] + [col for col in df.columns if col != 'DATE_TIME']]

            if my_download == 1:
                filename = campaign.slug + '_' + files_name.split('/')[-1][:-4] + '_df.dat'
                results = df

                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename=%s' % filename

                results.to_csv(path_or_buf=response, index=False)
                return response

            else:
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


@login_required
def graphs_raw_24h(request, slug):
    my_download = 0
    campaign = Campaign.objects.get(slug=slug)

    # form choices
    if campaign.raw_data_path:
        path = campaign.raw_data_path
        dirnames = glob.glob(path + '*/*/*')
        dirnames.sort(reverse=True)
        dates = list([filename[-10:] for filename in dirnames])
        date_choices = list(zip(dates, dates))

        # initial values
        days = dates[0]
        initial_data = {'days': days}

        # form
        raw_data_24h_form = DataRaw24hFormFunction(date_choices)
        form = raw_data_24h_form(request.POST or None, initial=initial_data)
        if form.is_valid():
            days = request.POST.get('days')
            if '_prev' in request.POST:
                days = (datetime.strptime(
                    days, '%Y/%m/%d') - timedelta(
                    days=1)).strftime('%Y/%m/%d')
                if days < date_choices[-1][0]:
                    days = date_choices[0][0]
                form = raw_data_24h_form(initial={'days': days})
            elif '_next' in request.POST:
                days = (datetime.strptime(
                    days, '%Y/%m/%d') + timedelta(
                    days=1)).strftime('%Y/%m/%d')
                if days > date_choices[0][0]:
                    days = date_choices[-1][0]
                form = raw_data_24h_form(initial={'days': days})
            elif '_download' in request.POST:
                my_download = 1

        # dataframe
        usecols = campaign.raw_var_list.split(',')
        dtype = campaign.raw_dtypes.split(',')
        dtype = dict(zip(usecols, dtype))
        filenames = [filename for filename in glob.iglob(
                path + days + '/*.dat')]
        filenames.sort()
        # ignoring last file as a temporary solution to broken line files
        # using "skipfooter" compromises the time of processing
        if days == dates[0]:
            filenames = filenames[:-1]
        if filenames:
            df = dd.read_csv(filenames,
                             sep=r'\s+',
                             usecols=usecols,
                             dtype=dtype,
                             engine='c',
                             )
            df = df.compute()
            df['DATE_TIME'] = pd.to_datetime(df['DATE'] + ' ' + df['TIME'])
            df = df.drop(['DATE', 'TIME'], axis=1)
            df = df[['DATE_TIME'] + [col for col in df.columns if col != 'DATE_TIME']]

            if my_download == 1:
                filename = campaign.slug + '_' + campaign.instrument.serial_number + \
                           '-' + days.replace('/', '') + '-DataLog_User_df.dat'
                results = df

                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename=%s' % filename

                results.to_csv(path_or_buf=response, index=False)
                return response

            else:
                script, div = bokeh_raw(df)
                context = {'campaign': campaign,
                           'form': form,
                           'script': script, 'div': div}
                return render(request, 'dashboard/ds_raw_24h.html', context)

        else:
            # form
            raw_data_24h_form = DataRaw24hFormFunction([('', 'no data available')])
            form = raw_data_24h_form(request.POST or None)
            context = {'campaign': campaign, 'form': form}
            return render(request, 'dashboard/ds_raw_24h.html', context)

    else:
        context = {'campaign': campaign}
        return render(request, 'dashboard/ds_raw_24h.html', context)


@login_required
def graphs_raw_24h_mobile(request, slug):
    my_download = 0
    campaign = Campaign.objects.get(slug=slug)

    # form choices
    if campaign.raw_data_path:
        path = campaign.raw_data_path
        dirnames = glob.glob(path + '*')
        dirnames.sort(reverse=True)
        dates = list([filename[-10:] for filename in dirnames])
        date_choices = list(zip(dates, dates))

        # initial values
        days = dates[0]
        initial_data = {'days': days}

        # form
        raw_data_24h_form = DataRaw24hFormFunction(date_choices)
        form = raw_data_24h_form(request.POST or None, initial=initial_data)
        if form.is_valid():
            days = request.POST.get('days')
            if '_prev' in request.POST:
                days = (datetime.strptime(
                    days, '%Y-%m-%d') - timedelta(
                    days=1)).strftime('%Y-%m-%d')
                if days < date_choices[-1][0]:
                    days = date_choices[0][0]
                form = raw_data_24h_form(initial={'days': days})
            elif '_next' in request.POST:
                days = (datetime.strptime(
                    days, '%Y-%m-%d') + timedelta(
                    days=1)).strftime('%Y-%m-%d')
                if days > date_choices[0][0]:
                    days = date_choices[-1][0]
                form = raw_data_24h_form(initial={'days': days})
            elif '_download' in request.POST:
                my_download = 1

        # dataframe
        usecols = campaign.raw_var_list.split(',')
        dtype = campaign.raw_dtypes.split(',')
        dtype = dict(zip(usecols, dtype))

        filenames = [filename for filename in glob.iglob(
                path + days + '/*_f*.txt')]

        if filenames:
            filenames.sort()
            df = dd.read_csv(filenames,
                             sep=',',
                             usecols=usecols,
                             dtype=dtype,
                             engine='c'
                             )
            df = df.compute()
            df['Time'] = pd.to_datetime(df['Time'], format="%m/%d/%Y%H:%M:%S.%f")

            if my_download == 1:
                filename = campaign.slug + '_' + campaign.instrument.serial_number + \
                           '_' + days.replace('-', '') + '_df.dat'
                results = df

                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename=%s' % filename

                results.to_csv(path_or_buf=response, index=False)
                return response

            else:
                script, div = bokeh_raw_mobile(df)
                context = {'campaign': campaign,
                           'form': form,
                           'script': script, 'div': div}
                return render(request, 'dashboard/ds_raw_24h.html', context)

        else:
            # form
            raw_data_24h_form = DataRaw24hFormFunction([('', 'no data available')])
            form = raw_data_24h_form(request.POST or None)
            context = {'campaign': campaign, 'form': form}
            return render(request, 'dashboard/ds_raw_24h.html', context)

    else:
        context = {'campaign': campaign}
        return render(request, 'dashboard/ds_raw_24h.html', context)
