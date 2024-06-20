from django import forms


def DataRawFormFunction(file_choices):

    class DataRawForm(forms.Form):
        files_name = forms.ChoiceField(
            widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
            choices=file_choices)

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
