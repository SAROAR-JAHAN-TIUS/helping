import os
from datetime import datetime, timedelta

import dateparser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def get_calendar_service():

    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )

            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build(
        "calendar",
        "v3",
        credentials=creds
    )


def create_calendar_event(item):

    service = get_calendar_service()

    title = item["title"]
    date_text = item["date"]
    start_time_text = item["start_time"]
    end_time_text = item.get("end_time")
    description = item.get("description", "")

    # Parse date
    if date_text.lower().startswith("next "):

        day_name = date_text[5:].strip().lower()

        weekdays = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6
        }

        today = datetime.now()

        target_day = weekdays[day_name]

        days_ahead = (target_day - today.weekday()) % 7

        if days_ahead == 0:
            days_ahead = 7

        event_date = today + timedelta(days=days_ahead)

    else:
        event_date = dateparser.parse(date_text)

    if not event_date:
        print(f"Could not parse date: {date_text}")
        return None

    # Parse start time
    start_time = datetime.strptime(
        start_time_text,
        "%I:%M %p"
    )

    start_datetime = event_date.replace(
        hour=start_time.hour,
        minute=start_time.minute,
        second=0,
        microsecond=0
    )

    # Parse end time
    if end_time_text:

        end_time = datetime.strptime(
            end_time_text,
            "%I:%M %p"
        )

        end_datetime = event_date.replace(
            hour=end_time.hour,
            minute=end_time.minute,
            second=0,
            microsecond=0
        )

    else:
        end_datetime = start_datetime + timedelta(hours=1)

    # Google Calendar event
    event = {
        "summary": title,
        "description": (
            f"{description}\n\n"
            f"Source timestamp: "
            f"{item.get('source_timestamp', 'N/A')}"
        ),
        "start": {
            "dateTime": start_datetime.isoformat(),
            "timeZone": "Asia/Dhaka"
        },
        "end": {
            "dateTime": end_datetime.isoformat(),
            "timeZone": "Asia/Dhaka"
        }
    }

    created_event = service.events().insert(
        calendarId="primary",
        body=event
    ).execute()

    return created_event