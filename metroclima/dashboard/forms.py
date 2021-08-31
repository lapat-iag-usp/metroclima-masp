from django import forms


def DataRawFormFunction(file_choices):

    class DataRawForm(forms.Form):
        files_name = forms.ChoiceField(widget=forms.Select(
            attrs={'class': 'form-select form-select-sm'}),
            choices=file_choices)

    return DataRawForm
