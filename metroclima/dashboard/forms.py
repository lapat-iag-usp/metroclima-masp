from django import forms

CAMPAIGN_CHOICES = [
    ('raw-data/unicid/G2401_CFKADS2348/DataLog_User/', 'UNICID G2401 201912 - DataLog_User'),
    ('raw-data/jaragua/G2301-m_CFADS2133/DataLog_User/', 'Pico do Jaraguá G2301-m 202103 - DataLog_User'),
    ('raw-data/jaragua/G2301_CFADS2502/DataLog_User/', 'Pico do Jaraguá G2301 II 202210 - DataLog_User'),
    ('raw-data/jaragua/G2301_CFADS2200/DataLog_User/', 'Pico do Jaraguá G2301 201901 - DataLog_User'),
    ('raw-data/jaragua/G2201-i_CFIDS2278/DataLog_User/', 'Pico do Jaraguá G2201-i 202406 - DataLog_User'),
    ('raw-data/icesp/G2311-f_CFHADS2050/DataLog_User/', 'ICESP G2311-f 202008 - DataLog_User'),
    ('raw-data/icesp/G2311-f_CFHADS2050/DataLog_User_Sync/', 'ICESP G2311-f 202008 - DataLog_User_Sync'),
    ('raw-data/iag/G2301-m_CFADS2133/DataLog_User/', 'IAG G2301-m 201901 - DataLog_User'),
    ('raw-data/iag/G2301_CFADS2502/DataLog_User/', 'IAG G2301 II 202003 - DataLog_User'),
    ('raw-data/iag/G2201-i_CFIDS2278/DataLog_User/', 'IAG G2201-i 202003 - DataLog_User'),
]


class MultiFileUploadForm(forms.Form):
    station = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        choices=CAMPAIGN_CHOICES,
        label='Selecione a campanha de medição')

    files = forms.FileField(widget=forms.ClearableFileInput(
        attrs={'class': 'form-control form-control-sm', 'multiple': True}), label='Selecione um ou mais arquivos')


class FolderUploadForm(forms.Form):
    station = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        choices=CAMPAIGN_CHOICES,
        label='Selecione a campanha de medição')

    files = forms.FileField(widget=forms.ClearableFileInput(
        attrs={'class': 'form-control form-control-sm', 'webkitdirectory': True, 'multiple': True}),
        label='Selecione uma pasta')


def YearFormFunction(years_choices):
    class YearForm(forms.Form):
        year = forms.ChoiceField(
            widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
            choices=years_choices, label="Select year")
    return YearForm


def DataRawFormFunction(files_choices_dict, year):
    files_choices = files_choices_dict[year]

    class DataRawForm(forms.Form):
        file = forms.ChoiceField(
            widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
            choices=files_choices)

    return DataRawForm


def DataRaw24hFormFunction(date_choices):

    class DataRaw24hForm(forms.Form):
        days = forms.ChoiceField(
            widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
            choices=date_choices)

    return DataRaw24hForm


def DataLevel0FormFunction(file_choices, variable_choices):

    class DataLevel0Form(forms.Form):
        files_name = forms.ChoiceField(
            widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
            choices=file_choices)
        variable_name = forms.ChoiceField(
            widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
            choices=variable_choices)

    return DataLevel0Form
