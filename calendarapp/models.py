from django.db import models
from django.contrib.auth.models import User

class CalendarEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event_id = models.CharField(max_length=100)
    summary = models.CharField(max_length=200)
    start_time = models.CharField(max_length=100)
    end_time = models.CharField(max_length=100)
    color = models.CharField(max_length=20, null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)