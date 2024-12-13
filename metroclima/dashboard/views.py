from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import TemplateView, DetailView, ListView
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, FileResponse
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from rest_framework.exceptions import APIException

import os
import glob
import io
import zipfile
import requests
from decouple import config, Csv
import dask.dataframe as dd
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import csv
import xarray as xr

from stations.models import Station, Instrument
from .models import Campaign, Event, Video
from .mygraphs import bokeh_raw, bokeh_raw_mobile, bokeh_level_0, data_overview_graph
from .forms import (DataRawFormFunction, DataRaw24hFormFunction, DataLevel0FormFunction,
                    YearFormFunction, MultiFileUploadForm, FolderUploadForm)


def is_in_group(user):
    return user.groups.filter(name='Upload').exists()


@user_passes_test(is_in_group)
def file_transfer(request):
    selected_station = None
    if request.method == 'POST':
        form = MultiFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('files')
            station = form.cleaned_data['station']
            selected_station = station
            success_files = []
            error_files = []

            for file in files:
                api_url = f"http://{config('ALLOWED_HOSTS', cast=Csv())[0]}/api_upload/upload/"
                file_data = {'file': file}
                headers = {'Authorization': f'Token {config("TOKEN")}',
                           'Station': station}

                response = requests.post(api_url, files=file_data, headers=headers)

                if response.status_code == 200:
                    success_files.append(file.name)
                else:
                    try:
                        error_message = response.json().get('detail', 'Erro desconhecido')
                    except ValueError:
                        error_message = 'Erro de resposta inválida da API'

                    error_files.append(f"{file.name} - {error_message}")
                    # error_files.append(file.name)

            if success_files:
                messages.success(request, "Arquivos enviados com sucesso:<br>" + "<br>".join(success_files))

            if error_files:
                messages.error(request, "Falha ao enviar os arquivos:<br>" + "<br>".join(error_files))

            form = MultiFileUploadForm(initial={'station': selected_station})

            return render(request, 'dashboard/ds_file_transfer.html', {'form': form})
    else:
        form = MultiFileUploadForm(initial={'station': selected_station})

        return render(request, 'dashboard/ds_file_transfer.html', {'form': form})


@user_passes_test(is_in_group)
def folder_transfer(request):
    selected_station = None
    if request.method == 'POST':
        form = FolderUploadForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('files')
            station = form.cleaned_data['station']
            selected_station = station
            success_files = []
            error_files = []

            for file in files:
                api_url = f"http://{config('ALLOWED_HOSTS', cast=Csv())[0]}/api_upload/upload/"
                file_data = {'file': file}
                headers = {'Authorization': f'Token {config("TOKEN")}',
                           'Station': station}

                response = requests.post(api_url, files=file_data, headers=headers)

                if response.status_code == 200:
                    success_files.append(file.name)
                else:
                    error_files.append(file.name)

            if success_files:
                messages.success(request, "Arquivos enviados com sucesso:<br>" + "<br>".join(success_files))

            if error_files:
                messages.error(request, "Falha ao enviar os arquivos:<br>" + "<br>".join(error_files))

            form = FolderUploadForm(initial={'station': selected_station})

            return render(request, 'dashboard/ds_folder_transfer.html', {'form': form})
    else:
        form = FolderUploadForm(initial={'station': selected_station})

        return render(request, 'dashboard/ds_folder_transfer.html', {'form': form})


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


def download_all_files(request, slug):
    campaign = get_object_or_404(Campaign, slug=slug)
    path = os.path.join(settings.MEDIA_ROOT, campaign.level_1_data_path)

    if not os.path.exists(path) or not os.path.isdir(path):
        return HttpResponseNotFound('Nenhum arquivo disponível para download.')

    # Cria um buffer em memória para o ZIP
    buffer = io.BytesIO()

    # Cria o ZIP no buffer
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file in os.listdir(path):
            full_file_path = os.path.join(path, file)
            if os.path.isfile(full_file_path):
                zf.write(full_file_path, os.path.basename(full_file_path))

    # Configura o buffer para o início
    buffer.seek(0)

    # Retorna o arquivo ZIP como resposta
    response = FileResponse(buffer, as_attachment=True, filename=f"{campaign.slug}_all_files.zip")
    return response


class DashboardUploadView(TemplateView):
    template_name = 'dashboard/ds_upload.html'


class DashboardDownloadView(TemplateView):
    template_name = 'dashboard/ds_download.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stations = Station.objects.all()
        grouped_campaigns = {
            station: station.campaign_set.filter(level_1_data_path__isnull=False)
            for station in stations
        }
        context['grouped_campaigns'] = grouped_campaigns
        return context


class DashboardDownloadFilesView(TemplateView):
    template_name = 'dashboard/ds_download_files.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign = get_object_or_404(Campaign, slug=kwargs['slug'])
        context['campaign'] = campaign

        path = os.path.join(settings.MEDIA_ROOT, campaign.level_1_data_path)
        if os.path.exists(path) and os.path.isdir(path):
            files_list = os.listdir(path)
            files_urls = [os.path.join(settings.MEDIA_URL, campaign.level_1_data_path, file) for file in files_list]
        else:
            files_list = []
            files_urls = []
        context['files'] = zip(files_list, files_urls)
        context['download_all_url'] = reverse('download_all_files', args=[campaign.slug])
        return context


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
        if campaign.raw_data_path and str(campaign.station) in ['UNICID', 'IAG', 'Pico do Jaraguá'] and str(campaign.instrument) != 'ABB':
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
                'station': [str(campaign.station)] * len(datetime_list),
                'date': datetime_list
            })
            dataframes.append(temp_df)
    df = pd.concat(dataframes, ignore_index=True)
    df = df.drop_duplicates()
    df.date = pd.to_datetime(df.date)
    script, div = data_overview_graph(df)
    context = {'script': script, 'div': div}
    return render(request, 'dashboard/ds_data_overview.html', context)


@login_required
def tutorials(request):
    videos = Video.objects.all()
    return render(request, 'dashboard/ds_tutorials.html', {'videos': videos})


@login_required
def graphs_raw(request, slug):
    my_download = 0
    invalid = 0
    campaign = Campaign.objects.get(slug=slug)
    start_dates = Event.objects.filter(logbook__slug='logbook-' + slug, invalid=True).values_list('start_date')
    end_dates = Event.objects.filter(logbook__slug='logbook-' + slug, invalid=True).values_list('end_date')
    start_dates = [my_date[0] for my_date in list(start_dates)]
    end_dates = [my_date[0] for my_date in list(end_dates)]

    if campaign.raw_data_path:
        path = campaign.raw_data_path
        filenames = [filename for filename in glob.iglob(
            path + '**/*.dat', recursive=True)]
        if filenames:
            filenames.sort(reverse=True)
            # ignoring last file as a temporary solution to broken line files
            # using "skipfooter" compromises the time of processing
            filenames = filenames[1:]
            names = [os.path.basename(filename) for filename in filenames]

            # form choices
            years_list = sorted(set([name.split('-')[1][:4] for name in names]), reverse=True)
            files_dict = {}
            for year in years_list:
                filtered_names = [name for name in names if name.split('-')[1].startswith(year)]
                filtered_filenames = [filename for filename in filenames if
                                      os.path.basename(filename) in filtered_names]
                files_dict[year] = list(zip(filtered_filenames, filtered_names))
            years_choices = list(zip(years_list, years_list))

            # initial forms
            year_form = YearFormFunction(years_choices)
            form_year = year_form(request.POST or None)
            form_file = None
            selected_file = None

            # forms
            if request.method == 'POST':
                form_year = year_form(request.POST)
                if form_year.is_valid():
                    selected_year = form_year.cleaned_data['year']
                    file_form = DataRawFormFunction(files_dict, selected_year)
                    form_file = file_form(request.POST)
                    if form_file.is_valid():
                        selected_file = form_file.cleaned_data['file']
                        action = request.POST.get('action')
                        idx_list = [name for name in names if name.split('-')[1].startswith(selected_year)]
                        files_list = [filename for filename in filenames if os.path.basename(filename) in idx_list]
                        idx = idx_list.index(os.path.basename(selected_file))
                        if action == 'previous' and idx < len(files_list) - 1:
                            selected_file = files_list[idx + 1]
                        elif action == 'next' and idx > 0:
                            selected_file = files_list[idx - 1]
                        form_file = file_form(initial={'file': selected_file})
                        if '_download' in request.POST:
                            my_download = 1
                        elif '_invalid' in request.POST:
                            invalid = 1

                        # dataframe
                        usecols = campaign.raw_var_list.split(',')
                        dtype = campaign.raw_dtypes.split(',')
                        dtype = dict(zip(usecols, dtype))
                        df = dd.read_csv(selected_file,
                                         sep=r'\s+',
                                         usecols=usecols,
                                         dtype=dtype,
                                         engine='c')
                        df = df.compute()
                        df['DATE_TIME'] = pd.to_datetime(df['DATE'] + ' ' + df['TIME'])
                        df = df.drop(['DATE', 'TIME'], axis=1)
                        df = df[['DATE_TIME'] + [col for col in df.columns if col != 'DATE_TIME']]

                        # download dataframe
                        if my_download == 1:
                            filename = campaign.slug + '_' + os.path.basename(selected_file)
                            results = df

                            response = HttpResponse(content_type='text/csv')
                            response['Content-Disposition'] = f'attachment; filename={filename}'

                            results.to_csv(path_or_buf=response, index=False)
                            return response

                        # remove invalid data
                        elif invalid == 1:
                            if invalid == 1:
                                for start_date, end_date in zip(start_dates, end_dates):
                                    df.loc[(df['DATE_TIME'] >= start_date.strftime("%Y-%m-%d %H:%M:%S")) &
                                           (df['DATE_TIME'] < end_date.strftime("%Y-%m-%d %H:%M:%S")), df.columns] = np.nan

                            script, div = bokeh_raw(df, start_dates, end_dates)
                            context = {'campaign': campaign,
                                       'form_year': form_year,
                                       'form_file': form_file,
                                       'selected_file': selected_file,
                                       'script': script, 'div': div}
                            return render(request, 'dashboard/ds_raw.html', context)

                        script, div = bokeh_raw(df, start_dates, end_dates)
                        context = {'campaign': campaign,
                                   'form_year': form_year,
                                   'form_file': form_file,
                                   'selected_file': selected_file,
                                   'script': script, 'div': div}
                        return render(request, 'dashboard/ds_raw.html', context)

            context = {'campaign': campaign,
                       'form_year': form_year,
                       'form_file': form_file,
                       'selected_file': selected_file}
            return render(request, 'dashboard/ds_raw.html', context)

        else:  # no filenames
            year_form = YearFormFunction([('', 'no data available')])
            form_year = year_form(request.POST or None)
            context = {'campaign': campaign,
                       'form_year': form_year}
            return render(request, 'dashboard/ds_raw.html', context)

    else:  # no campaign
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

