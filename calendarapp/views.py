from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from .models import CalendarEvent
from datetime import datetime, timedelta
import pickle
import os
from django.utils.timezone import localtime
from dateutil import tz
import re

def extract_first_email(text):
    email_pattern = re.compile(r"""
        [a-zA-Z0-9._%+-]+   # username
        @                   # @ symbol
        [a-zA-Z0-9.-]+      # domain name
        \.[a-zA-Z]{2,}      # dot-something
    """, re.VERBOSE)
    email_list = email_pattern.findall(text)
    if len(email_list)==0:
        return None
    else:
        return email_list[0]

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
    # print(os.getcwd())
    with open(os.path.join(os.getcwd(),'token.pickle'), 'rb') as token:
        creds = pickle.load(token)
    # creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/calendar.readonly'])
    service = build('calendar', 'v3', credentials=creds)
    # now = datetime.datetime.utcnow().isoformat() + 'Z'
    current_month = datetime.now().strftime('%Y-%m')
    selected_month = request.GET.get('month',current_month)
    # print(selected_month)
    timezone = timedelta(hours=6)
    try:
        YEAR, MONTH = selected_month.split('-')
        YEAR, MONTH = int(YEAR), int(MONTH)
    except:
        now = datetime.now()
        YEAR = int(now.year)
        MONTH = int(now.month)
        selected_month = f"{YEAR}-{MONTH}"
    if MONTH != 12:
        tmax = datetime(YEAR,MONTH+1,1) + timezone
        tmin = datetime(YEAR,MONTH,1,1) + timezone
        # nod = tmax-tmin
    else:
        tmax = datetime(YEAR+1,1,1) + timezone
        tmin = datetime(YEAR,12,1) + timezone
        # nod = tmax-tmin
    # nod = int((tmax-2*timezone).day)
    tmax = tmax.isoformat() + 'Z'
    tmin = tmin.isoformat() + 'Z'
    # print('Number of days in this month is ', nod)

    events_result = service.events().list(calendarId='fbl0k2sutrlprdgc7sk5rcss3g@group.calendar.google.com', 
                                        timeMin=tmin,
                                        timeMax=tmax, 
                                        singleEvents=True,
                                        maxResults=10000, 
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])


    # CalendarEvent.objects.filter(
    #             user=request.user,
    #             start_time__startswith=selected_month
    #         ).delete()

    # Store events in the database
    for event in events:
        # get email
        first_email = extract_first_email(event.get('summary', 'No Title'))
        if first_email is None:
            continue
    
        start_time = event['start'].get('dateTime', event['start'].get('date'))
        end_time = event['end'].get('dateTime', event['end'].get('date'))
        # Convert to local time zone
        local_tz = tz.tzlocal()

        # Convert to datetime objects and calculate duration
        start_dt = datetime.fromisoformat(start_time).astimezone(local_tz)
        end_dt = datetime.fromisoformat(end_time).astimezone(local_tz)
        duration = end_dt - start_dt
        duration_in_minutes = round(duration.total_seconds() / 60,1)
        
        CalendarEvent.objects.update_or_create(
            user=request.user,
            event_id=event['id'],
            defaults={
                'summary': event.get('summary', 'No Title'),
                'start_time':start_dt.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end_dt.strftime('%Y-%m-%d %H:%M:%S'),
                'color': event.get('colorId', None),
                'duration': duration_in_minutes 
            }
        )

    # Filter by month
    # selected_month = request.GET.get('month')
    selected_color = request.GET.get('color',5)
    search_query = request.GET.get('search_query', '')
    
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
    
    if search_query:
        events = events.filter(summary__icontains=search_query)  # Case-insensitive search

    total_duration = sum(event.duration for event in events) if events else 0
    # print(total_duration)
    # Get sorting column and direction
    sort_by = request.GET.get("sort_by", "start_time")  # Default to start_time
    order = request.GET.get("order", "asc")

    # Apply sorting
    if order == "asc":
        events = events.order_by(sort_by)
    else:
        events = events.order_by(f"-{sort_by}")

    

    context = {
        'events': events,
        'sort_by': sort_by,
        'order': order,
        'selected_month': selected_month,
        'search_query': search_query,
        'total_duration': total_duration,  # Pass the total duration to the template
    }
    return render(request, 'calendar.html', context)

