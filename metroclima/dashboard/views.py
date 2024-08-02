from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, DetailView
from django.shortcuts import render
from django.http import HttpResponse
import os
import glob
import dask.dataframe as dd
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import csv
import xarray as xr

from stations.models import Station, Instrument
from .models import Campaign, Event
from .mygraphs import bokeh_raw, bokeh_raw_mobile, bokeh_level_0, data_overview_graph
from .forms import DataRawFormFunction, DataRaw24hFormFunction, DataLevel0FormFunction


def export_logbook_csv(request, slug):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="{}"'.format('logbook-' + slug + '.csv')

    writer = csv.writer(response)
    writer.writerow([
        'name', 'event_date', 'description', 'invalid', 'start_date', 'end_date', 'flags', 'revised'])

    events = Event.objects.filter(logbook__slug='logbook-' + slug).values_list(
        'name', 'event_date', 'description', 'invalid', 'start_date', 'end_date', 'flags__flag', 'revised')
    for event in events:
        writer.writerow(event)

    return response


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
def data_overview(request):
    campaigns = Campaign.objects.all()
    dataframes = []
    for campaign in campaigns:
        if campaign.raw_data_path and str(campaign.station) in ['IAG', 'Pico do Jaraguá'] and str(campaign.instrument) != 'ABB':
            path = campaign.raw_data_path
            filenames = [os.path.basename(filename) for filename in glob.iglob(path + '**/*.dat', recursive=True)]
            datetime_list = []
            for filename in filenames:
                date_time_str = filename.split('-')[1] + ' ' + filename.split('-')[2]
                date_time_obj = datetime.strptime(date_time_str, '%Y%m%d %H%M%SZ')
                datetime_list.append(date_time_obj.strftime('%Y-%m-%d %H'))
            datetime_list.sort()
            temp_df = pd.DataFrame({
                'campaign': [campaign.name] * len(datetime_list),
                'date': datetime_list
            })
            dataframes.append(temp_df)
    df = pd.concat(dataframes, ignore_index=True)
    df.date = pd.to_datetime(df.date)
    script, div = data_overview_graph(df)
    context = {'script': script, 'div': div}
    return render(request, 'dashboard/ds_home.html', context)


@login_required
def graphs_raw(request, slug):
    my_download = 0
    invalid = 0
    campaign = Campaign.objects.get(slug=slug)
    start_dates = Event.objects.filter(logbook__slug='logbook-' + slug, invalid=True).values_list('start_date')
    end_dates = Event.objects.filter(logbook__slug='logbook-' + slug, invalid=True).values_list('end_date')
    start_dates = [my_date[0] for my_date in list(start_dates)]
    end_dates = [my_date[0] for my_date in list(end_dates)]

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
                elif '_invalid' in request.POST:
                    invalid = 1

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
                if invalid == 1:
                    for start_date, end_date in zip(start_dates, end_dates):
                        df.loc[(df['DATE_TIME'] >= start_date.strftime("%Y-%m-%d %H:%M:%S")) &
                               (df['DATE_TIME'] < end_date.strftime("%Y-%m-%d %H:%M:%S")), df.columns] = np.nan

                script, div = bokeh_raw(df, start_dates, end_dates)
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
    invalid = 0
    campaign = Campaign.objects.get(slug=slug)
    start_dates = Event.objects.filter(logbook__slug='logbook-' + slug, invalid=True).values_list('start_date')
    end_dates = Event.objects.filter(logbook__slug='logbook-' + slug, invalid=True).values_list('end_date')
    start_dates = [my_date[0] for my_date in list(start_dates)]
    end_dates = [my_date[0] for my_date in list(end_dates)]

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
            elif '_invalid' in request.POST:
                invalid = 1

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

            if 'species' in df.columns:
                # TODO: The specie value is subject to change and should be configurable by the user
                df = df[df.species == 1]
                df = df.drop(['species'], axis=1)

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
                if invalid == 1:
                    for start_date, end_date in zip(start_dates, end_dates):
                        df.loc[(df['DATE_TIME'] >= start_date.strftime("%Y-%m-%d %H:%M:%S")) &
                               (df['DATE_TIME'] < end_date.strftime("%Y-%m-%d %H:%M:%S")), df.columns] = np.nan

                script, div = bokeh_raw(df, start_dates, end_dates)
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
    invalid = 0
    campaign = Campaign.objects.get(slug=slug)
    start_dates = Event.objects.filter(logbook__slug='logbook-' + slug, invalid=True).values_list('start_date')
    end_dates = Event.objects.filter(logbook__slug='logbook-' + slug, invalid=True).values_list('end_date')
    start_dates = [my_date[0] for my_date in list(start_dates)]
    end_dates = [my_date[0] for my_date in list(end_dates)]

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
            elif '_invalid' in request.POST:
                invalid = 1


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
                if invalid == 1:
                    for start_date, end_date in zip(start_dates, end_dates):
                        df.loc[(df['Time'] >= start_date.strftime("%Y-%m-%d %H:%M:%S")) &
                               (df['Time'] <= end_date.strftime("%Y-%m-%d %H:%M:%S")), df.columns] = np.nan

                script, div = bokeh_raw_mobile(df, start_dates, end_dates)
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
def graphs_level_0(request, slug):
    my_download = 0
    invalid = 0
    campaign = Campaign.objects.get(slug=slug)

    # form choices
    if campaign.level_0_data_path:
        path = str(campaign.level_0_data_path)
        filenames = [filename for filename in glob.iglob(os.path.join(path, '*.nc'), recursive=True)]
        if filenames:
            filenames.sort(reverse=True)
            file_choices = list(
                zip(filenames,
                    [os.path.basename(filename) for filename in filenames]))

            # initial values
            files_name = filenames[0]

            # dataset
            # ds = xr.open_dataset(files_name)
            # exclude_vars = {"time", "FM", "FA", "CAL"}
            # variable_choices = [(var, var) for var in ds.data_vars.keys() if var not in exclude_vars]
            # variable_name = next((var for var, _ in variable_choices if "CO2" in var), variable_choices[0][0])
            # initial_data = {'files_name': files_name, 'variable_name': variable_name}
            # ds.close()

            # NOTE: Temporary fix!
            variable_choices = [('CO2', 'CO2'), ('CO2_dry', 'CO2_dry'),
                                ('CH4', 'CH4'), ('CH4_dry', 'CH4_dry'),
                                ('H2O', 'H2O'),
                                ('solenoid_valves', 'solenoid_valves'),
                                ('MPVPosition', 'MPVPosition'),
                                ('CavityTemp', 'CavityTemp'),
                                ('CavityPressure', 'CavityPressure')]
            variable_name = 'CO2'
            initial_data = {'files_name': files_name, 'variable_name': variable_name}

            # form
            raw_data_form = DataLevel0FormFunction(file_choices, variable_choices)
            form = raw_data_form(request.POST or None, initial=initial_data)
            if form.is_valid():
                files_name = request.POST.get('files_name')
                variable_name = request.POST.get('variable_name')
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
                elif '_invalid' in request.POST:
                    invalid = 1

            # TODO: Think in a better solution than opening the dataset twice!
            ds = xr.open_dataset(files_name)

            if my_download == 1:
                pass

            else:
                if invalid == 1:
                    mask = (ds['FM'] == 0) & (ds['FA'] == 0) & (ds['CAL'] == 0)
                    ds[variable_name] = ds[variable_name].where(mask)

                script, div = bokeh_level_0(ds, variable_name)
                context = {'campaign': campaign,
                           'form': form,
                           'script': script, 'div': div}
                return render(request, 'dashboard/ds_level_0.html', context)

        else:
            # form
            raw_data_form = DataLevel0FormFunction([('', 'no data available')], [('', 'no data available')])
            form = raw_data_form(request.POST or None)
            context = {'campaign': campaign, 'form': form}
            return render(request, 'dashboard/ds_level_0.html', context)

    else:
        context = {'campaign': campaign}
        return render(request, 'dashboard/ds_level_0.html', context)

