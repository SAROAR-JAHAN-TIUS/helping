from fastapi import FastAPI
import json
from calender_set import create_calendar_event
from fastapi.responses import FileResponse
import os
from fastapi.middleware.cors import CORSMiddleware
import threading
from system_audio import stop_transcription,start_transcription
from meeting_processing import process_meeting
from search import ask_meeting
from pydantic import BaseModel
from date_time import extract_calendar_events
from google.oauth2 import id_token
from google.auth.transport import requests
import uuid
from fastapi import Depends
from sqlalchemy.orm import Session
from datetime import datetime
from database import Base, engine, get_db
from database_models import User, Meeting, Participant
from fastapi import WebSocket, WebSocketDisconnect
meeting_connections = {}
meeting_thread = None
class GoogleLoginRequest(BaseModel):
    credential: str
class ChatMessage(BaseModel):
    role: str
    content: str
class CreateMeetingRequest(BaseModel):
    user_id: str
class JoinMeetingRequest(BaseModel):
    meeting_id: str
class MeetingQuestion(BaseModel):
    question: str
    history: list[ChatMessage] = []
app=FastAPI(
        title="Meeting AI",
        description="A FastAPI application for analyzing meeting transcripts and extracting events.",
        version="1.0.0 "
)
Base.metadata.create_all(bind=engine)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.get("/transcript")
def get_transcript():
    with open("transcript.json", "r", encoding="utf-8") as file:
        transcript = json.load(file)

    return transcript
@app.post("/meetings/{meeting_id}/start")
def start_meeting(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    global meeting_thread

    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id
    ).first()

    if not meeting:
        return {
            "success": False,
            "message": "Meeting not found"
        }

    if meeting.status == "ended":
        return {
            "success": False,
            "message": "Meeting has already ended"
        }

    if meeting_thread and meeting_thread.is_alive():
        return {
            "success": False,
            "message": "Transcription is already running"
        }

    meeting.status = "active"
    db.commit()

    meeting_thread = threading.Thread(
        target=start_transcription,
        daemon=True
    )

    meeting_thread.start()

    return {
        "success": True,
        "message": "Meeting started and transcription started",
        "meeting_id": meeting_id
    }

@app.post("/meeting/stop")
def stop_meeting():
    global meeting_thread

    stop_transcription()

    if meeting_thread:
        meeting_thread.join()
        meeting_thread = None

    process_meeting()
    extract_calendar_events()
    return {
        "success": True,
        "message": "Meeting processed successfully",
        "event": "Calendar events extracted and processed.",
        
        "files": {
            "meeting_report": "/files/meeting_report.pdf",
            "full_conversation": "/files/full_conversation.pdf"
        }
    }
@app.post("/meeting/ask")
def ask_meeting_question(data: MeetingQuestion):

    history = [
        {
            "role": message.role,
            "content": message.content
        }
        for message in data.history
    ]

    return ask_meeting(
        data.question,
        history
    )
@app.post("/meeting/test")
def test_meeting():
    process_meeting()

    return {
        "success": True,
        "message": "Test meeting processed"
    }
@app.get("/meeting/report")
def get_meeting_report():
    file_path = "meeting_report.pdf"

    if not os.path.exists(file_path):
        return {"success": False, "message": "Meeting report not found."}

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename="meeting_report.pdf"
    )


@app.get("/meeting/full-conversation")
def get_full_conversation():
    file_path = "full_conversation.pdf"

    if not os.path.exists(file_path):
        return {"success": False, "message": "Full conversation PDF not found."}

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename="full_conversation.pdf"
    )
@app.post("/auth/google")
def google_login(data: GoogleLoginRequest,db :Session = Depends(get_db)):
    try:
        user_info = id_token.verify_oauth2_token(
            data.credential,    
            requests.Request(),
            os.getenv("GOOGLE_CLIENT_ID")
        )
        google_id = user_info["sub"]
        name = user_info.get("name")
        email = user_info.get("email")
        picture = user_info.get("picture")
        user=db.query(User).filter(User.id == google_id).first()
        if not user :
            user =User(
                id=google_id,
                name=name,
                email=email,
                picture=picture
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return {
            "success": True,
            "user": {
                "google_id": user_info["sub"],
                "name": user_info.get("name"),
                "email": user_info.get("email"),
                "picture": user_info.get("picture")
            }
        }
    except ValueError as e:
        return {
            "success": False,
            "message": "Invalid Google credentials",
            "error": str(e)
        }
@app.post("/meetings/create")
def create_meeting(
    data: CreateMeetingRequest,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.id == data.user_id
    ).first()

    if not user:
        return {
            "success": False,
            "message": "User not found"
        }

    meeting_id = str(uuid.uuid4())[:8]

    meeting = Meeting(
        id=meeting_id,
        host_user_id=user.id,
        status="waiting"
    )

    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    return {
        "success": True,
        "meeting": {
            "meeting_id": meeting.id,
            "host": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        }
    }

@app.post("/meetings/{meeting_id}/join")
def join_meeting(
    meeting_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):

    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id
    ).first()

    if not meeting:
        return {
            "success": False,
            "message": "Meeting not found"
        }

    if meeting.status == "ended":
        return {
            "success": False,
            "message": "Meeting has ended"
        }

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        return {
            "success": False,
            "message": "User not found"
        }

    participant = Participant(
        id=str(uuid.uuid4()),
        meeting_id=meeting_id,
        user_id=user_id
    )

    db.add(participant)
    db.commit()
    db.refresh(participant)
    host_participant = Participant(
    id=str(uuid.uuid4()),
    meeting_id=meeting.id,
    user_id=user.id
    )

    db.add(host_participant)
    db.commit()
    return {
        "success": True,
        "participant": {
            "id": participant.id,
            "user_id": user.id,
            "name": user.name,
            "email": user.email
        }
    }
@app.post("/meetings/{meeting_id}/leave")
def leave_meeting(
    meeting_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    participant = db.query(Participant).filter(
        Participant.meeting_id == meeting_id,
        Participant.user_id == user_id,
        Participant.left_at == None
    ).first()

    if not participant:
        return {
            "success": False,
            "message": "Participant not found"
        }

    participant.left_at = datetime.utcnow()

    db.commit()

    return {
        "success": True,
        "message": "Left meeting"
    }

@app.post("/meetings/{meeting_id}/end")
def end_meeting(
    meeting_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    global meeting_thread

    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id
    ).first()

    if not meeting:
        return {
            "success": False,
            "message": "Meeting not found"
        }

    if meeting.host_user_id != user_id:
        return {
            "success": False,
            "message": "Only the host can end the meeting"
        }

    if meeting.status == "ended":
        return {
            "success": False,
            "message": "Meeting has already ended"
        }

    # Stop AssemblyAI transcription
    stop_transcription()

    if meeting_thread:
        meeting_thread.join()
        meeting_thread = None

    # Mark meeting as ended
    meeting.status = "ended"

    db.commit()

    # Process transcript
    process_meeting()

    # Extract calendar events
    extract_calendar_events()

    return {
        "success": True,
        "message": "Meeting ended and processed successfully",
        "meeting_id": meeting_id,
        "files": {
            "meeting_report": "/meeting/report",
            "full_conversation": "/meeting/full-conversation"
        }
    }
@app.websocket("/ws/meeting/{meeting_id}")
async def meeting_websocket(
    websocket: WebSocket,
    meeting_id: str
):
    await websocket.accept()

    if meeting_id not in meeting_connections:
        meeting_connections[meeting_id] = []

    meeting_connections[meeting_id].append(websocket)

    try:
        while True:
            message = await websocket.receive_json()

            for connection in meeting_connections[meeting_id]:
                if connection != websocket:
                    await connection.send_json(message)

    except WebSocketDisconnect:

        if meeting_id in meeting_connections:

            if websocket in meeting_connections[meeting_id]:
                meeting_connections[meeting_id].remove(websocket)

            if not meeting_connections[meeting_id]:
                del meeting_connections[meeting_id]