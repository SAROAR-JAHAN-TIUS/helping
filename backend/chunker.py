import json
from datetime import timedelta

CHUNK_DURATION = timedelta(minutes=5)
OVERLAP = timedelta(minutes=1)
STEP = CHUNK_DURATION - OVERLAP


def timestamp_to_seconds(timestamp):
    hours, minutes, seconds = map(int, timestamp.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def seconds_to_timestamp(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


with open("transcript.json", "r", encoding="utf-8") as file:
    transcript = json.load(file)


# Convert transcript timestamps to seconds
for item in transcript:
    item["_start_seconds"] = timestamp_to_seconds(item["start"])


chunks = []

chunk_start = 0


while True:

    chunk_end = chunk_start + CHUNK_DURATION.total_seconds()

    current_chunk = [
        item
        for item in transcript
        if chunk_start <= item["_start_seconds"] < chunk_end
    ]

    if not current_chunk:
        break

    chunk_text = "\n".join(
        f"[{item['start']}] {item['speaker']}: {item['text']}"
        for item in current_chunk
    )

    chunks.append({
        "chunk_id": len(chunks) + 1,
        "start": seconds_to_timestamp(int(chunk_start)),
        "end": current_chunk[-1]["end"],
        "text": chunk_text,
        "entries": current_chunk
    })

    chunk_start += STEP.total_seconds()


with open("chunks.json", "w", encoding="utf-8") as file:
    json.dump(chunks, file, indent=4, ensure_ascii=False)


print(f"Total chunks: {len(chunks)}")

for chunk in chunks:
    print(
        f"Chunk {chunk['chunk_id']}: "
        f"{chunk['start']} → {chunk['end']} "
        f"({len(chunk['entries'])} entries)"
    )