import subprocess
import os 
import json
from dotenv import load_dotenv
import threading

stop_event = threading.Event()
load_dotenv()
transcript = []

from assemblyai.streaming.v3 import (
    RealTimeEvents,
    RealTimeTranscriber,
    RealTimeParameters,
    RealTimeTranscriberOptions,
    TurnEvent,
    BeginEvent,TerminationEvent,RealTimeError,
)
API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
if not API_KEY:
    raise RuntimeError("ASSEMBLYAI_API_KEY environment variable is not set.")
DEVICE = "bluez_output.F4:B6:2D:58:A9:27.monitor"
def on_begin(client, event: BeginEvent):
    print(f"Connected. Session ID: {event.id}")
    print("Listening to system audio...\n")
def format_timestamp(ms):
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = total_seconds // 60
    seconds = total_seconds % 60

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"    
def on_turn(client, event):
    if event.end_of_turn:
        start = event.words[0].start
        end = event.words[-1].end

        print(
            f"\nSpeaker {event.speaker_label} "
            f"[{format_timestamp(start)} - {format_timestamp(end)}]: "
            f"{event.transcript}"
        )

        transcript.append({
             "speaker": event.speaker_label,
            #  "start_ms": event.words[0].start,
            #  "end_ms": event.words[-1].end,
             "start": format_timestamp(event.words[0].start),
             "end": format_timestamp(event.words[-1].end),
             "text": event.transcript
        })

        with open("transcript.json", "w", encoding="utf-8") as file:
            json.dump(transcript, file, indent=4, ensure_ascii=False)

    else:
        print(f"PARTIAL: {event.transcript}", end="\r")
def on_terminated(client, event: TerminationEvent):
    print("\nAssemblyAI session ended.")
def on_error(client, error: RealTimeError):
    print(f"\nAssemblyAI error: {error}")
def start_transcription():
    stop_event.clear()
    client = RealTimeTranscriber(
        api_key=API_KEY,
        options=RealTimeTranscriberOptions(),
    )

    client.on(RealTimeEvents.Begin, on_begin)
    client.on(RealTimeEvents.Turn, on_turn)
    client.on(RealTimeEvents.Termination, on_terminated)
    client.on(RealTimeEvents.Error, on_error)

    client.connect(
        RealTimeParameters(
            sample_rate=16000,
            speech_model="universal-3-5-pro",
            speaker_labels=True,
            max_speakers=3,
            language_code="en",
        )
    )

    command = [
        "ffmpeg",
        "-f", "pulse",
        "-i", DEVICE,
        "-f", "s16le",
        "-ac", "1",
        "-ar", "16000",
        "-"
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=0,
    )
    record_command = [
        "ffmpeg",
        "-y",
        "-f", "pulse",
        "-i", DEVICE,
        "-c:a", "libopus",
        "-b:a", "128k",
        "meeting_recording.webm"
    ]

    record_process = subprocess.Popen(
        record_command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print("System audio → AssemblyAI")
    print("Play speech/audio now.")

    try:
        while not stop_event.is_set():

            audio_chunk = process.stdout.read(3200)

            if not audio_chunk:
                break

            client.stream(audio_chunk)

    finally:
        process.terminate()
        process.wait()

        client.disconnect(terminate=True)
        record_process.terminate()
        record_process.wait()

        print("Disconnected.")


def stop_transcription():
    stop_event.set()