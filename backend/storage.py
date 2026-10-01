import os
from pathlib import Path

MEETINGS_DIR = Path(os.getenv("MEETINGS_STORAGE_DIR", "meetings"))


def get_meeting_dir(meeting_id: str) -> Path:
    meeting_dir = MEETINGS_DIR / meeting_id
    meeting_dir.mkdir(parents=True, exist_ok=True)
    return meeting_dir


def get_meeting_file(meeting_id: str, filename: str) -> Path:
    return get_meeting_dir(meeting_id) / filename
