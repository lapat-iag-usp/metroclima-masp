from django import forms


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
