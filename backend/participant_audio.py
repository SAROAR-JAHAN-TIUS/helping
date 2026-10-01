import os
import json
import threading

from dotenv import load_dotenv
from assemblyai.streaming.v3 import (
    RealTimeEvents,
    RealTimeTranscriber,
    RealTimeParameters,
    RealTimeTranscriberOptions,
    BeginEvent,
    TerminationEvent,
    RealTimeError,
)

from storage import get_meeting_file

load_dotenv()

API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
if not API_KEY:
    raise RuntimeError("ASSEMBLYAI_API_KEY environment variable is not set.")


class ParticipantTranscriber:
    def __init__(self, meeting_id, user_id, name):
        self.meeting_id = meeting_id
        self.user_id = user_id
        self.name = name
        self.client = None
        self.lock = threading.Lock()
        self.running = False

    def on_begin(self, client, event: BeginEvent):
        print(f"[Transcriber] {self.name} connected. Session ID: {event.id}")

    def on_turn(self, client, event):
        if not event.end_of_turn:
            return
        if not event.words:
            return

        start_ms = event.words[0].start
        end_ms = event.words[-1].end

        entry = {
            "meeting_id": self.meeting_id,
            "user_id": self.user_id,
            "speaker": self.name,
            "start": self.format_timestamp(start_ms),
            "end": self.format_timestamp(end_ms),
            "text": event.transcript
        }

        print(f"[Transcriber] {self.name} [{entry['start']} - {entry['end']}]: {entry['text']}")
        self.save_transcript(entry)

    def on_terminated(self, client, event: TerminationEvent):
        print(f"[Transcriber] {self.name} AssemblyAI session ended.")

    def on_error(self, client, error: RealTimeError):
        print(f"[Transcriber] {self.name} AssemblyAI error: {error}")

    @staticmethod
    def format_timestamp(ms):
        total_seconds = ms // 1000
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def save_transcript(self, entry):
        filename = get_meeting_file(
            self.meeting_id,
            f"transcript_{self.user_id}.json"
        )

        with self.lock:
            try:
                with open(filename, "r", encoding="utf-8") as file:
                    transcript = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                transcript = []

            transcript.append(entry)

            with open(filename, "w", encoding="utf-8") as file:
                json.dump(transcript, file, indent=4, ensure_ascii=False)

    def start(self):
        if self.running:
            return
        self.running = True

        self.client = RealTimeTranscriber(
            api_key=API_KEY,
            options=RealTimeTranscriberOptions(),
        )

        self.client.on(RealTimeEvents.Begin, self.on_begin)
        self.client.on(RealTimeEvents.Turn, self.on_turn)
        self.client.on(RealTimeEvents.Termination, self.on_terminated)
        self.client.on(RealTimeEvents.Error, self.on_error)

        self.client.connect(
            RealTimeParameters(
                sample_rate=16000,
                speech_model="universal-3-5-pro",
                speaker_labels=True,
            )
        )

        print(f"[Transcriber] {self.name} started for meeting {self.meeting_id}.")

    def stream(self, audio_bytes):
        if not self.running or not self.client:
            return
        try:
            self.client.stream(audio_bytes)
        except Exception as e:
            print(f"[Transcriber] {self.name} Error streaming audio: {e}")

    def stop(self):
        if not self.running:
            return
        self.running = False

        if self.client:
            try:
                self.client.disconnect(terminate=True)
            except Exception as e:
                print(f"[Transcriber] {self.name} Error disconnecting: {e}")
            self.client = None

        print(f"[Transcriber] {self.name} stopped for meeting {self.meeting_id}.")


active_transcribers = {}


def start_participant_transcriber(meeting_id, user_id, name):
    key = (str(meeting_id), str(user_id))

    if key in active_transcribers:
        return active_transcribers[key]

    transcriber = ParticipantTranscriber(meeting_id, user_id, name)
    transcriber.start()
    active_transcribers[key] = transcriber
    return transcriber


def get_participant_transcriber(meeting_id, user_id):
    key = (str(meeting_id), str(user_id))
    return active_transcribers.get(key)


def stop_participant_transcriber(meeting_id, user_id):
    key = (str(meeting_id), str(user_id))
    transcriber = active_transcribers.pop(key, None)
    if transcriber:
        transcriber.stop()


def stop_all_meeting_transcribers(meeting_id):
    meeting_id = str(meeting_id)
    keys_to_remove = [
        key for key in active_transcribers
        if key[0] == meeting_id
    ]
    for key in keys_to_remove:
        transcriber = active_transcribers.pop(key, None)
        if transcriber:
            transcriber.stop()


def merge_meeting_transcripts(meeting_id: str):
    """Merge all per-participant transcripts into a single transcript.json sorted by time."""
    from storage import get_meeting_dir
    import glob

    meeting_dir = get_meeting_dir(meeting_id)
    pattern = str(meeting_dir / "transcript_*.json")
    files = glob.glob(pattern)

    all_entries = []

    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                entries = json.load(f)
                all_entries.extend(entries)
        except (json.JSONDecodeError, FileNotFoundError):
            continue

    # Sort by start timestamp
    def timestamp_to_ms(ts):
        parts = ts.split(":")
        if len(parts) == 3:
            h, m, s = map(int, parts)
            return h * 3600000 + m * 60000 + s * 1000
        return 0

    all_entries.sort(key=lambda e: timestamp_to_ms(e.get("start", "00:00:00")))

    output_file = get_meeting_file(meeting_id, "transcript.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, indent=4, ensure_ascii=False)

    print(f"Merged {len(all_entries)} entries from {len(files)} participants into transcript.json")
    return all_entries