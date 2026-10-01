import json
import os
import threading
import uuid
from datetime import datetime

from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests

from database import Base, engine, get_db, init_db
from database_models import User, Meeting, Participant
from storage import get_meeting_file, get_meeting_dir
from meeting_processing import process_meeting
from search import ask_meeting
from calender_set import create_calendar_event
from participant_audio import (
    start_participant_transcriber,
    get_participant_transcriber,
    stop_participant_transcriber,
    stop_all_meeting_transcribers,
    merge_meeting_transcripts,
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class GoogleLoginRequest(BaseModel):
    credential: str


class ChatMessage(BaseModel):
    role: str
    content: str


class CreateMeetingRequest(BaseModel):
    user_id: str
    title: str = "Untitled Meeting"


class MeetingQuestion(BaseModel):
    question: str
    history: list[ChatMessage] = []


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Meeting AI",
    description="Sakkhat Meeting AI API",
    version="1.0.0"
)

init_db()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory WebSocket connections: {meeting_id: {user_id: {"socket": ws, "name": str}}}
meeting_connections: dict = {}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/")
def home():
    return {"message": "Welcome to the Sakkhat Meeting AI API!"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@app.post("/auth/google")
def google_login(data: GoogleLoginRequest, db: Session = Depends(get_db)):
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

        user = db.query(User).filter(User.id == google_id).first()

        if not user:
            user = User(
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
                "google_id": google_id,
                "name": name,
                "email": email,
                "picture": picture
            }
        }

    except ValueError as e:
        return {
            "success": False,
            "message": "Invalid Google credentials",
            "error": str(e)
        }


# ---------------------------------------------------------------------------
# Meetings CRUD
# ---------------------------------------------------------------------------

@app.post("/meetings/create")
def create_meeting(data: CreateMeetingRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == data.user_id).first()

    if not user:
        return {"success": False, "message": "User not found"}

    meeting_id = str(uuid.uuid4())[:8]

    meeting = Meeting(
        id=meeting_id,
        title=data.title,
        host_user_id=user.id,
        status="waiting"
    )

    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    host_participant = Participant(
        id=str(uuid.uuid4()),
        meeting_id=meeting_id,
        user_id=user.id,
        joined_at=datetime.utcnow(),
        left_at=None
    )

    db.add(host_participant)
    db.commit()

    # Create meeting storage directory
    get_meeting_dir(meeting_id)

    return {
        "success": True,
        "meeting": {
            "meeting_id": meeting.id,
            "title": meeting.title,
            "host": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        }
    }


@app.post("/meetings/{meeting_id}/join")
def join_meeting(meeting_id: str, user_id: str, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()

    if not meeting:
        return {"success": False, "message": "Meeting not found"}

    if meeting.status in ("ended", "ending", "processing", "completed"):
        return {"success": False, "message": "Meeting has ended"}

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return {"success": False, "message": "User not found"}

    existing = db.query(Participant).filter(
        Participant.meeting_id == meeting_id,
        Participant.user_id == user_id,
        Participant.left_at == None
    ).first()

    if existing:
        return {
            "success": True,
            "message": "Already joined",
            "participant": {
                "id": existing.id,
                "user_id": user.id,
                "name": user.name,
                "email": user.email
            }
        }

    participant = Participant(
        id=str(uuid.uuid4()),
        meeting_id=meeting_id,
        user_id=user_id,
        joined_at=datetime.utcnow()
    )

    db.add(participant)
    db.commit()
    db.refresh(participant)

    return {
        "success": True,
        "participant": {
            "id": participant.id,
            "user_id": user.id,
            "name": user.name,
            "email": user.email
        }
    }


# ---------------------------------------------------------------------------
# Leave meeting
# ---------------------------------------------------------------------------

@app.post("/meetings/{meeting_id}/leave")
async def leave_meeting(meeting_id: str, user_id: str, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()

    if not meeting:
        return {"success": False, "message": "Meeting not found"}

    participant = db.query(Participant).filter(
        Participant.meeting_id == meeting_id,
        Participant.user_id == user_id,
        Participant.left_at == None
    ).first()

    if not participant:
        return {"success": False, "message": "Not in this meeting"}

    participant.left_at = datetime.utcnow()
    db.commit()

    # Stop this participant's transcriber
    stop_participant_transcriber(meeting_id, user_id)

    # Broadcast to other participants via WebSocket if connected
    if meeting_id in meeting_connections:
        for other_id, info in list(meeting_connections[meeting_id].items()):
            if other_id != user_id:
                try:
                    await info["socket"].send_json({
                        "type": "participant-left",
                        "user_id": user_id
                    })
                except Exception:
                    pass

    return {
        "success": True,
        "message": "Left the meeting"
    }


# ---------------------------------------------------------------------------
# End meeting (host only)
# ---------------------------------------------------------------------------

@app.post("/meetings/{meeting_id}/end")
async def end_meeting(meeting_id: str, user_id: str, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()

    if not meeting:
        return {"success": False, "message": "Meeting not found"}

    if meeting.status in ("ending", "processing", "completed"):
        return {"success": False, "message": "Meeting already ended"}

    if meeting.host_user_id != user_id:
        return {"success": False, "message": "Only the host can end the meeting"}

    # Transition to ending
    meeting.status = "ending"
    meeting.ended_at = datetime.utcnow()

    if meeting.created_at:
        delta = meeting.ended_at - meeting.created_at
        meeting.duration_seconds = int(delta.total_seconds())

    db.commit()

    # Mark all active participants as left
    active_participants = db.query(Participant).filter(
        Participant.meeting_id == meeting_id,
        Participant.left_at == None
    ).all()

    for p in active_participants:
        p.left_at = meeting.ended_at

    db.commit()

    # Broadcast meeting-ended to ALL connected WebSocket clients!
    if meeting_id in meeting_connections:
        for p_user_id, info in list(meeting_connections[meeting_id].items()):
            try:
                await info["socket"].send_json({
                    "type": "meeting-ended",
                    "meeting_id": meeting_id
                })
            except Exception as e:
                print(f"Error broadcasting meeting-ended: {e}")

    # Stop all transcribers and merge transcripts
    stop_all_meeting_transcribers(meeting_id)

    # Check if there are per-participant transcripts to merge
    try:
        merged = merge_meeting_transcripts(meeting_id)
        has_transcript = len(merged) > 0
    except Exception as e:
        print(f"Merge transcripts error: {e}")
        has_transcript = False

    if has_transcript:
        # Run processing in background thread
        meeting.status = "processing"
        db.commit()

        def run_processing():
            try:
                process_meeting(meeting_id)
                # Update status to completed
                from database import SessionLocal
                session = SessionLocal()
                try:
                    m = session.query(Meeting).filter(Meeting.id == meeting_id).first()
                    if m:
                        m.status = "completed"
                        session.commit()
                finally:
                    session.close()
                print(f"Meeting {meeting_id} processing complete.")
            except Exception as e:
                print(f"Meeting {meeting_id} processing error: {e}")
                from database import SessionLocal
                session = SessionLocal()
                try:
                    m = session.query(Meeting).filter(Meeting.id == meeting_id).first()
                    if m:
                        m.status = "completed"
                        session.commit()
                finally:
                    session.close()

        thread = threading.Thread(target=run_processing, daemon=True)
        thread.start()
    else:
        meeting.status = "completed"
        db.commit()

    return {
        "success": True,
        "message": "Meeting ended",
        "has_transcript": has_transcript
    }


# ---------------------------------------------------------------------------
# Meeting status / results
# ---------------------------------------------------------------------------

@app.get("/meetings/{meeting_id}/status")
def get_meeting_status(meeting_id: str, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()

    if not meeting:
        return {"success": False, "message": "Meeting not found"}

    participants = db.query(Participant).filter(
        Participant.meeting_id == meeting_id
    ).all()

    # Get participant names from User table
    participant_list = []
    for p in participants:
        user = db.query(User).filter(User.id == p.user_id).first()
        participant_list.append({
            "user_id": p.user_id,
            "name": user.name if user else "Unknown",
            "joined_at": p.joined_at.isoformat() if p.joined_at else None,
            "left_at": p.left_at.isoformat() if p.left_at else None
        })

    return {
        "success": True,
        "meeting": {
            "id": meeting.id,
            "title": meeting.title,
            "host_user_id": meeting.host_user_id,
            "status": meeting.status,
            "created_at": meeting.created_at.isoformat() if meeting.created_at else None,
            "ended_at": meeting.ended_at.isoformat() if meeting.ended_at else None,
            "duration_seconds": meeting.duration_seconds,
            "participants": participant_list
        }
    }


@app.get("/meetings/{meeting_id}/results")
def get_meeting_results(meeting_id: str, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()

    if not meeting:
        return {"success": False, "message": "Meeting not found"}

    analysis_file = get_meeting_file(meeting_id, "meeting_analysis.json")
    events_file = get_meeting_file(meeting_id, "extracted_events.json")
    transcript_file = get_meeting_file(meeting_id, "transcript.json")

    analysis = None
    events = None
    transcript = None

    if os.path.exists(analysis_file):
        with open(analysis_file, "r", encoding="utf-8") as f:
            analysis = json.load(f)

    if os.path.exists(events_file):
        with open(events_file, "r", encoding="utf-8") as f:
            events = json.load(f)

    if os.path.exists(transcript_file):
        with open(transcript_file, "r", encoding="utf-8") as f:
            transcript = json.load(f)

    report_exists = os.path.exists(get_meeting_file(meeting_id, "meeting_report.pdf"))
    conversation_exists = os.path.exists(get_meeting_file(meeting_id, "full_conversation.pdf"))

    return {
        "success": True,
        "status": meeting.status,
        "analysis": analysis,
        "events": events,
        "transcript": transcript,
        "has_report": report_exists,
        "has_conversation_pdf": conversation_exists
    }


# ---------------------------------------------------------------------------
# Per-meeting file endpoints
# ---------------------------------------------------------------------------

@app.get("/meetings/{meeting_id}/report")
def get_meeting_report(meeting_id: str):
    file_path = get_meeting_file(meeting_id, "meeting_report.pdf")

    if not os.path.exists(file_path):
        return {"success": False, "message": "Meeting report not found."}

    return FileResponse(
        str(file_path),
        media_type="application/pdf",
        filename="meeting_report.pdf"
    )


@app.get("/meetings/{meeting_id}/full-conversation")
def get_full_conversation(meeting_id: str):
    file_path = get_meeting_file(meeting_id, "full_conversation.pdf")

    if not os.path.exists(file_path):
        return {"success": False, "message": "Full conversation PDF not found."}

    return FileResponse(
        str(file_path),
        media_type="application/pdf",
        filename="full_conversation.pdf"
    )


@app.get("/meetings/{meeting_id}/transcript")
def get_meeting_transcript(meeting_id: str):
    file_path = get_meeting_file(meeting_id, "transcript.json")

    if not os.path.exists(file_path):
        return {"success": False, "message": "Transcript not found."}

    with open(file_path, "r", encoding="utf-8") as f:
        transcript = json.load(f)

    return {"success": True, "transcript": transcript}


@app.get("/meetings/{meeting_id}/calendar-events")
def get_meeting_calendar_events(meeting_id: str):
    file_path = get_meeting_file(meeting_id, "extracted_events.json")

    if not os.path.exists(file_path):
        return {"success": True, "events": []}

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


@app.post("/meetings/{meeting_id}/calendar-events/{event_id}/confirm")
def confirm_calendar_event(meeting_id: str, event_id: int):
    file_path = get_meeting_file(meeting_id, "extracted_events.json")

    if not os.path.exists(file_path):
        return {"success": False, "message": "No events found."}

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    events = data.get("events", [])

    if event_id < 0 or event_id >= len(events):
        return {"success": False, "message": "Invalid event ID."}

    event = events[event_id]
    created_event = create_calendar_event(event)

    if not created_event:
        return {"success": False, "message": "Could not create calendar event."}

    return {
        "success": True,
        "message": "Event created successfully.",
        "event": created_event.get("htmlLink")
    }


# ---------------------------------------------------------------------------
# AskAI per meeting
# ---------------------------------------------------------------------------

@app.post("/meetings/{meeting_id}/ask")
def ask_meeting_question(meeting_id: str, data: MeetingQuestion):
    history = [
        {"role": message.role, "content": message.content}
        for message in data.history
    ]

    return ask_meeting(meeting_id, data.question, history)


# ---------------------------------------------------------------------------
# Meeting history
# ---------------------------------------------------------------------------

@app.get("/meetings/history")
def get_meeting_history(user_id: str, db: Session = Depends(get_db)):
    # Get all meetings where user is a participant
    participations = db.query(Participant).filter(
        Participant.user_id == user_id
    ).all()

    meeting_ids = list(set(p.meeting_id for p in participations))

    meetings = db.query(Meeting).filter(
        Meeting.id.in_(meeting_ids)
    ).order_by(Meeting.created_at.desc()).all()

    result = []
    for meeting in meetings:
        participants = db.query(Participant).filter(
            Participant.meeting_id == meeting.id
        ).all()

        participant_names = []
        for p in participants:
            user = db.query(User).filter(User.id == p.user_id).first()
            if user:
                participant_names.append(user.name)

        result.append({
            "id": meeting.id,
            "title": meeting.title,
            "status": meeting.status,
            "created_at": meeting.created_at.isoformat() if meeting.created_at else None,
            "ended_at": meeting.ended_at.isoformat() if meeting.ended_at else None,
            "duration_seconds": meeting.duration_seconds,
            "host_user_id": meeting.host_user_id,
            "participants": participant_names
        })

    return {"success": True, "meetings": result}


# ---------------------------------------------------------------------------
# WebSocket signaling + audio
# ---------------------------------------------------------------------------

@app.websocket("/ws/meeting/{meeting_id}")
async def meeting_websocket(websocket: WebSocket, meeting_id: str):
    await websocket.accept()

    if meeting_id not in meeting_connections:
        meeting_connections[meeting_id] = {}

    connections = meeting_connections[meeting_id]

    user_id = None
    user_name = None

    try:
        # First message must identify the participant (JSON hello)
        hello = await websocket.receive_json()

        if hello.get("type") != "hello":
            await websocket.close()
            return

        user_id = str(hello.get("user_id"))
        user_name = hello.get("name", "Participant")

        # Send existing participants to new user
        existing_participants = []
        for existing_user_id, info in connections.items():
            existing_participants.append({
                "user_id": existing_user_id,
                "name": info["name"]
            })

        await websocket.send_json({
            "type": "existing-participants",
            "participants": existing_participants
        })

        # Register new participant
        connections[user_id] = {
            "socket": websocket,
            "name": user_name
        }

        print(f"User joined WebSocket: {user_name} ({user_id}) meeting={meeting_id}")

        # Start audio transcriber for this participant
        try:
            start_participant_transcriber(meeting_id, user_id, user_name)
        except Exception as e:
            print(f"Could not start transcriber for {user_name}: {e}")

        # Tell everyone else about the new participant
        for other_user_id, info in connections.items():
            if other_user_id != user_id:
                try:
                    await info["socket"].send_json({
                        "type": "participant-joined",
                        "user_id": user_id,
                        "name": user_name
                    })
                except Exception:
                    pass

        # Signaling loop - handles both JSON and binary messages
        while True:
            message = await websocket.receive()

            # Binary data = audio PCM
            if "bytes" in message and message["bytes"]:
                audio_data = message["bytes"]
                transcriber = get_participant_transcriber(meeting_id, user_id)
                if transcriber:
                    transcriber.stream(audio_data)
                continue

            # JSON data = signaling
            if "text" in message and message["text"]:
                try:
                    data = json.loads(message["text"])
                except json.JSONDecodeError:
                    continue

                target = data.get("target")

                if target:
                    target = str(target)
                    target_info = connections.get(target)
                    if target_info:
                        data["from"] = user_id
                        try:
                            await target_info["socket"].send_json(data)
                        except Exception:
                            pass
                else:
                    data["from"] = user_id
                    for other_user_id, info in connections.items():
                        if other_user_id != user_id:
                            try:
                                await info["socket"].send_json(data)
                            except Exception:
                                pass

    except WebSocketDisconnect:
        print(f"User disconnected: {user_name} ({user_id})")

    except Exception as e:
        print(f"WebSocket error for {user_name}: {e}")

    finally:
        # Stop transcriber for this participant
        if user_id:
            stop_participant_transcriber(meeting_id, user_id)

        if meeting_id in meeting_connections:
            connections = meeting_connections[meeting_id]

            if user_id and user_id in connections:
                del connections[user_id]

            # Tell remaining participants
            for other_user_id, info in connections.items():
                try:
                    await info["socket"].send_json({
                        "type": "participant-left",
                        "user_id": user_id
                    })
                except Exception:
                    pass

            if not connections:
                del meeting_connections[meeting_id]

        print(f"WebSocket cleanup complete: {meeting_id}")