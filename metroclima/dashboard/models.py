from django.db import models
from django.template.defaultfilters import slugify

from stations.models import Station, Instrument


class Campaign(models.Model):
    name = models.CharField(max_length=250, blank=True, null=True)
    station = models.ForeignKey(Station, on_delete=models.SET_NULL, blank=True, null=True)
    instrument = models.ForeignKey(Instrument, on_delete=models.SET_NULL, blank=True, null=True)
    date = models.DateField(help_text="Please use the following format: YYYY-MM-DD.", null=True)
    raw_data_path = models.CharField(max_length=250, blank=True, null=True)
    level_0_data_path = models.CharField(max_length=250, blank=True, null=True)
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


class Flag(models.Model):
    flag = models.CharField(max_length=3)
    description = models.TextField(max_length=500)

    def __str__(self):
        return self.flag


class Logbook(models.Model):
    name = models.CharField(max_length=50)
    station = models.ForeignKey(Station, on_delete=models.CASCADE, blank=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = "Logbook " + self.campaign.name
        self.slug = slugify(self.name)
        return super().save(*args, **kwargs)


class Event(models.Model):
    name = models.CharField(max_length=50, blank=True)
    logbook = models.ForeignKey(Logbook, on_delete=models.CASCADE)
    event_date = models.DateField(help_text="Please use the following format: YYYY-MM-DD.")
    description = models.TextField(max_length=1000)
    invalid = models.BooleanField(default=False)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    flags = models.ForeignKey(Flag, on_delete=models.CASCADE, null=True, blank=True)
    revised = models.BooleanField(default=False)
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        qs = Event.objects.filter(event_date=self.event_date)
        if not qs:
            n = 1
        else:
            my_list = ([int(str(event)[-2:]) for event in qs])
            n = sorted(my_list)[-1] + 1
        if not self.name:
            self.name = self.logbook.name + " " + str(self.event_date) + " " + f"{n:02d}"
        else:
            self.name = self.name
        self.slug = slugify(self.name)
        return super().save(*args, **kwargs)


def event_file_path(instance, filename):
    qs = EventFile.objects.filter(event=instance.event)
    if not qs:
        n = 1
    else:
        my_list = ([int(str(event).split('.')[0][-2:]) for event in qs])
        n = sorted(my_list)[-1] + 1
    ext = filename.split('.')[-1]
    filename = f"files/logbook/{str(instance.event.logbook).replace(' ', '_')}/{instance.event.name}_file{n:02d}.{ext}"
    return filename


class EventFile(models.Model):
    file = models.FileField(upload_to=event_file_path)
    description = models.CharField(max_length=500)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    def __str__(self):
        return self.file.url

    def delete(self, *args, **kwargs):
        storage, path = self.file.storage, self.file.path
        super(EventFile, self).delete(*args, **kwargs)
        storage.delete(path)
