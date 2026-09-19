import os

from dotenv import load_dotenv
import pyaudio

from assemblyai.streaming.v3 import (
    RealTimeEvents,
    RealTimeParameters,
    RealTimeTranscriber,
    RealTimeTranscriberOptions,
    TurnEvent,
    BeginEvent,
    TerminationEvent,
    RealTimeError,
)


load_dotenv()

API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

if not API_KEY:
    raise RuntimeError("ASSEMBLYAI_API_KEY not found")


SAMPLE_RATE = 16000
CHANNELS = 1
FRAMES_PER_BUFFER = 800


def on_begin(client: RealTimeTranscriber, event: BeginEvent):
    print(f"\nConnected. Session ID: {event.id}")
    print("Speak now...\n")


def on_turn(client: RealTimeTranscriber, event: TurnEvent):
    if event.end_of_turn:
        print(f"FINAL: {event.transcript}")
    else:
        print(f"PARTIAL: {event.transcript}", end="\r")


def on_terminated(client: RealTimeTranscriber, event: TerminationEvent):
    print(
        f"\nSession ended. "
        f"Processed {event.audio_duration_seconds:.2f} seconds."
    )


def on_error(client: RealTimeTranscriber, error: RealTimeError):
    print(f"\nAssemblyAI error: {error}")


client = RealTimeTranscriber(
    RealTimeTranscriberOptions(),
    api_key=API_KEY,
)

client.on(RealTimeEvents.Begin, on_begin)
client.on(RealTimeEvents.Turn, on_turn)
client.on(RealTimeEvents.Termination, on_terminated)
client.on(RealTimeEvents.Error, on_error)


client.connect(
    RealTimeParameters(
        sample_rate=SAMPLE_RATE,
        speech_model="universal-3-5-pro",
    )
)


audio = pyaudio.PyAudio()

microphone = audio.open(
    format=pyaudio.paInt16,
    channels=CHANNELS,
    rate=SAMPLE_RATE,
    input=True,
    frames_per_buffer=FRAMES_PER_BUFFER,
)

try:
    while True:
        data = microphone.read(
            FRAMES_PER_BUFFER,
            exception_on_overflow=False,
        )

        client.stream(data)

except KeyboardInterrupt:
    print("\nStopping...")

finally:
    microphone.stop_stream()
    microphone.close()
    audio.terminate()

    client.disconnect(terminate=True)
    print("Disconnected.")
