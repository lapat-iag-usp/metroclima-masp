from django.db import models
from django.template.defaultfilters import slugify

from stations.models import Station, Instrument


class Campaign(models.Model):
    name = models.CharField(max_length=250, blank=True, null=True)
    station = models.ForeignKey(Station, on_delete=models.SET_NULL, blank=True, null=True)
    instrument = models.ForeignKey(Instrument, on_delete=models.SET_NULL, blank=True, null=True)
    date = models.DateField(help_text="Please use the following format: YYYY-MM-DD.", null=True)
    raw_data_path = models.CharField(max_length=250, blank=True, null=True)
    raw_var_list = models.CharField(max_length=250, blank=True, null=True)
    raw_dtypes = models.CharField(max_length=250, blank=True, null=True)
    mobile_campaign = models.BooleanField(default=False)
    place = models.CharField(max_length=250, null=True, blank=True)
    description = models.TextField(max_length=1000, blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.mobile_campaign:
            self.name = self.instrument.name + " " + self.place + " " + str(self.date).replace('-', '')
            self.slug = slugify(self.name)
            return super().save(*args, **kwargs)
        else:
            self.name = self.station.name + " " + self.instrument.name + " " + str(self.date).replace('-', '')[:-2]
            self.slug = slugify(self.name)
            return super().save(*args, **kwargs)


class CampaignFile(models.Model):
    file = models.FileField(upload_to="files/campaign/")
    description = models.CharField(max_length=500)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)

    def __str__(self):
        return self.file.url

    def delete(self, *args, **kwargs):
        storage, path = self.file.storage, self.file.path
        super(CampaignFile, self).delete(*args, **kwargs)
        storage.delete(path)

