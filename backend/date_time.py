import json
from dotenv import load_dotenv
from openai import OpenAI
import os
load_dotenv()
API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
if not API_KEY:
    raise RuntimeError("ASSEMBLYAI_API_KEY is not set.")
client =OpenAI(
    api_key=API_KEY,
    base_url="https://llm-gateway.assemblyai.com/v1")
with open ("test.json", "r", encoding="utf-8") as f:
    transcript = json.load(f)
conversation_parts = []
for entry in transcript:
   speaker=entry.get("speaker", "Unknown")
   start=entry.get("start", "")
   text=entry.get("text", "")
   conversation_parts.append(f"[{start}] {speaker}: {text}")
conversation = "\n".join(conversation_parts)
prompt = f"""
You are a meeting date and time extraction assistant.

Analyze the meeting transcript and identify any future events,
meetings, deadlines, appointments, launches, or other scheduled
activities that are explicitly mentioned.

IMPORTANT RULES:

1. Only extract dates, days, and times that are supported by the transcript.
2. Never invent a date or time.
3. Never assume a year unless it can be safely determined.
4. Extract relative expressions such as:
   - tomorrow
   - next Monday
   - next Friday
   - next week
   - at 3 PM
5. Preserve the original meaning of the date/time.
6. Separate the date expression from the time expression.
7. If the transcript says "next Thursday at 4:30 PM",
   return:
   date: "next Thursday"
   start_time: "4:30 PM"
8. If only a date/day is mentioned, set start_time to JSON null.
9. If only a time is mentioned, set date to JSON null.
10. Use actual JSON null, not the string "null".
11. Do not put the date expression inside start_time.
12. Do not put the time expression inside date.
13. If no future event is mentioned, return an empty events list.
14. Include the transcript timestamp where the event was mentioned.
15. Return ONLY valid JSON.

Return this structure:

{{
    "events": [
        {{
            "title": "short event title",
            "date": "date expression from transcript or null",
            "start_time": "time expression from transcript or null",
            "end_time": "time expression from transcript or null",
            "description": "short polished description based only on the transcript",
            "source_timestamp": "transcript timestamp"
        }}
    ]
}}

If no future event is found:

{{
    "events": []
}}

Meeting transcript:

{conversation}
"""
response = client.chat.completions.create(
    model="qwen3.5-4b-32k-fast",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ],
    max_tokens=1500
)
result = response.choices[0].message.content

result = result.strip()

if result.startswith("```json"):
    result = result[7:]

if result.startswith("```"):
    result = result[3:]

if result.endswith("```"):
    result = result[:-3]

result = result.strip()

data = json.loads(result)
with open("extracted_events.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print ("\nExtracted events saved to extracted_events.json")    