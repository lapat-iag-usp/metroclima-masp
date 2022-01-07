from django.db import models
from django.template.defaultfilters import slugify


class Instrument(models.Model):
    instrument = models.CharField(max_length=50)
    measuring = models.CharField(max_length=50)
    serial_number = models.CharField(max_length=50, null=True)
    mobile_campaign = models.BooleanField(default=False)
    slug = models.SlugField(unique=True, blank=True, null=True)

    def __str__(self):
        return self.instrument + " " + self.serial_number

    def save(self, *args, **kwargs):
        self.slug = slugify(self.instrument)
        return super().save(*args, **kwargs)


class InstrumentFile(models.Model):
    file = models.FileField(upload_to="instruments/files/")
    description = models.CharField(max_length=500)
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)

    def __str__(self):
        return self.file.url

    def delete(self, *args, **kwargs):
        storage, path = self.file.storage, self.file.path
        super(InstrumentFile, self).delete(*args, **kwargs)
        storage.delete(path)


class Station(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=500)
    latitude = models.DecimalField(max_digits=11, decimal_places=6)
    longitude = models.DecimalField(max_digits=11, decimal_places=6)
    elevation = models.DecimalField(max_digits=4, decimal_places=0)
    inlet_elevation = models.DecimalField(max_digits=3, decimal_places=0, blank=True, null=True)
    picture = models.ImageField(upload_to='stations/pictures/', blank=True, null=True)
    video = models.FileField(upload_to='stations/videos/', blank=True, null=True)
    instruments = models.ManyToManyField('Instrument', blank=True)
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.video.delete()
        super().delete(*args, **kwargs)


class Image(models.Model):
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='stations/images/')
    alt = models.CharField(max_length=100)
    panoramic = models.BooleanField()

    def __str__(self):
        return self.image.url

    def delete(self, *args, **kwargs):
        self.image.delete()
        super().delete(*args, **kwargs)
