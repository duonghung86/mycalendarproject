from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from .models import CalendarEvent
import datetime
import pickle
import os
# Login view
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('calendar_view')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# Logout view
def logout_view(request):
    logout(request)
    return redirect('login')

# Calendar view
@login_required
def calendar_view(request):
    # Load Google Calendar events
    print(os.getcwd())
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
    # creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/calendar.readonly'])
    service = build('calendar', 'v3', credentials=creds)
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(calendarId='fbl0k2sutrlprdgc7sk5rcss3g@group.calendar.google.com', timeMin=now, singleEvents=True,maxResults=10000, orderBy='startTime').execute()
    events = events_result.get('items', [])

    # Store events in the database
    for event in events:
        CalendarEvent.objects.update_or_create(
            user=request.user,
            event_id=event['id'],
            defaults={
                'summary': event.get('summary', 'No Title'),
                'start_time': event['start'].get('dateTime', event['start'].get('date')),
                'end_time': event['end'].get('dateTime', event['end'].get('date')),
                'color': event.get('colorId', None)
            }
        )

    # Filter by month
    selected_month = request.GET.get('month')
    selected_color = request.GET.get('color')

    if selected_month and selected_color:
        events = CalendarEvent.objects.filter(
            user=request.user,
            start_time__startswith=selected_month,
            color=selected_color
        )
    elif selected_month:
        events = CalendarEvent.objects.filter(
            user=request.user,
            start_time__startswith=selected_month
        )
    elif selected_color:
        events = CalendarEvent.objects.filter(
            user=request.user,
            color=selected_color
        )
    else:
        events = CalendarEvent.objects.filter(user=request.user)

    context = {'events': events, 'selected_month': selected_month, 'selected_color': selected_color}
    return render(request, 'calendar.html', context)
