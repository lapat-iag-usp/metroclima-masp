from django.db import models


class Group(models.Model):
    group = models.CharField(max_length=50)
    order = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return self.group


class Institution(models.Model):
    institution = models.CharField(max_length=50)

    def __str__(self):
        return self.institution


class Member(models.Model):
    name = models.CharField(max_length=50)
    group = models.ForeignKey('Group', on_delete=models.SET_NULL, null=True)
    institution = models.ForeignKey('Institution', on_delete=models.SET_NULL, null=True)
    google = models.CharField(max_length=100, blank=True, null=True)
    orcid = models.CharField(max_length=100, blank=True, null=True)
    lattes = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name
