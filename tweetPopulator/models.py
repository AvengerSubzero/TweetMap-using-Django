from __future__ import unicode_literals

from django.db import models

from geoposition.fields import GeopositionField

class Tweets(models.Model):
    id = models.IntegerField(primary_key=True)
    text = models.TextField()
    position = GeopositionField(null=True)
    place = models.TextField()
    country = models.TextField()
    date = models.DateTimeField()
