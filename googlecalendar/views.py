import os
import json
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from django.http import HttpResponseRedirect
from django.conf import settings
from django.views import View

import datetime
from django.http import JsonResponse

class GoogleCalendarInitView(View):
    def get(self, request):
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            os.path.join(settings.BASE_DIR, 'credentials.json'),
            scopes=['https://www.googleapis.com/auth/calendar.readonly']
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        request.session['google_auth_state'] = state
        return HttpResponseRedirect(authorization_url)


class GoogleCalendarRedirectView(View):
    def get(self, request):
        state = request.session.get('google_auth_state')
        if state is None:
            # Handle error: Invalid state
            pass

        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            os.path.join(settings.BASE_DIR, 'credentials.json'),
            scopes=['https://www.googleapis.com/auth/calendar.readonly'],
            state=state
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

        authorization_response = request.build_absolute_uri()
        flow.fetch_token(authorization_response=authorization_response)

        credentials = flow.credentials
        request.session['google_credentials'] = credentials_to_dict(credentials)
        
        # Once you have the credentials, you can use them to fetch the list of events from the user's calendar
        
        service = build('calendar', 'v3', credentials=credentials)

        # Fetch the list of events from the user's primary calendar
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = service.events().list(calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        # Process the events and prepare the response
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            event_list.append({
                'summary': event['summary'],
                'start': start,
                'end': end,
            })

        return JsonResponse({'events': event_list})

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes,
    }
