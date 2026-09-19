from fastapi import FastAPI
import json
from calender_set import create_calendar_event
from search import ask_question

app=FastAPI(
        title="Meeting AI",
        description="A FastAPI application for analyzing meeting transcripts and extracting events.",
        version="1.0.0 "
)
@app.get("/")
def home():
    return {"message": "Welcome to the Meeting AI API!"}
@app.get("/health")
def health_check():
    return {"status": "healthy"}
@app.get("/meeting-analysis")
def get_meeting_analysis():

    with open("meeting_analysis.json", "r", encoding="utf-8") as file:
        analysis = json.load(file)

    return analysis
@app.get("/calendar-events")
def get_calendar_events():

    with open("extracted_events.json", "r", encoding="utf-8") as file:
        events = json.load(file)

    return events
@app.post("/create-calendar-event/{event_id}/confirm")
def confirm_calendar_event(event_id: int):
    with open("extracted_events.json", "r", encoding="utf-8") as file:
        events = json.load(file)

    events =events.get("events", [])
    if event_id < 0 or event_id >= len(events):
        return {
            "success": False,
            "message": "Invalid event ID."
        }

    event = events[event_id]
    created_event = create_calendar_event(event)
    return{
        "success ": True,
        "message": "Event created successfully.",
        "event": created_event.get("htmlLink")
    }
@app.get("/ask-question")
def ask_qmeeting(question: str):
    return ask_question(question)
@app.get("/transcript")
def get_transcript():
    with open("transcript.json", "r", encoding="utf-8") as file:
        transcript = json.load(file)

    return transcript