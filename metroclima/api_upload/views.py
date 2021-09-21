from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.files.storage import FileSystemStorage
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FileUploadParser
from rest_framework.exceptions import APIException
import os
import pathlib


class FileUploadView(APIView):
    permission_classes = (IsAuthenticated,)
    parser_class = (FileUploadParser,)

    def post(self, request):
        context = {}
        uploaded_file = request.FILES['file']
        context['name_file'] = uploaded_file.name
        context['name_size'] = uploaded_file.size
        station = request.META['HTTP_STATION']

        # check if Sync or not and correct date indexes
        n = 0 if uploaded_file.name.endswith('DataLog_User.dat') else 5

        # identify year, month and day from uploaded file to create directories
        year = uploaded_file.name[-33 - n:-29 - n]
        month = uploaded_file.name[-29 - n:-27 - n]
        day = uploaded_file.name[-27 - n:-25 - n]

        # check valid dates
        if not 2010 <= int(year) <= 2030:
            raise APIException("Year is not valid!")
        if not 1 <= int(month) <= 12:
            raise APIException("Month is not valid!")
        if not 1 <= int(day) <= 31:
            raise APIException("Day is not valid!")

        context['path'] = './media/' + station \
            + year + '/' + month + '/' + day + '/'
        pathlib.Path(context['path']).mkdir(parents=True, exist_ok=True)

        # if same file by name > check the size
        if context['name_file'] in os.listdir(context['path']):
            file_name = context['path'] + context['name_file']
            # if new file is bigger > remove old file
            if context['name_size'] > os.path.getsize(file_name):
                # remove file from system to replace with new file
                os.remove(file_name)
                fs = FileSystemStorage()
                name = fs.save(file_name[8:], uploaded_file)
                context['url'] = fs.url(name)
                return Response(context)
            else:
                return Response(context)
        else:
            fs = FileSystemStorage()
            file_name = context['path'] + context['name_file']
            name = fs.save(file_name[8:], uploaded_file)
            context['url'] = fs.url(name)
            print(file_name[8:])
            print(file_name)
            return Response(context)
