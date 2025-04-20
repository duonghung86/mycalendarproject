from django.db import models
from django.contrib.auth.models import User

class CalendarEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event_id = models.CharField(max_length=100)
    summary = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    color = models.CharField(max_length=20, null=True, blank=True)