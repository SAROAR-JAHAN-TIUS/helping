import json 
import os

from dotenv import load_dotenv
from openai import OpenAI

from models import MeetingAnalysis

load_dotenv()

API_KEY = os.getenv("ASSEMBLYAI_API_KEY")


if not API_KEY:
    raise RuntimeError("ASSEMBLYAI_API_KEY is not set.")
input_file = "transcript.json" 
output_file = "meeting_analysis.json"
client = OpenAI(
    api_key=API_KEY,
    base_url="https://llm-gateway.assemblyai.com/v1"
)
if not os.path.exists(input_file):
    raise FileNotFoundError(
        f"{input_file} was not found."
    )

with open(input_file, "r", encoding="utf-8") as file:
    transcript = json.load(file)



if not transcript:
    raise ValueError("transcript.json is empty.")

conversation_parts = []

for item in transcript:

    speaker = item.get("speaker", "UNKNOWN")
    start = item.get("start", "")
    end = item.get("end", "")
    text = item.get("text", "")

    conversation_parts.append(
        f"[{start} - {end}] "
        f"Speaker {speaker}: {text}"
    )

conversation = "\n".join(conversation_parts)

prompt = f"""
You are an AI meeting analyst.

Analyze the meeting transcript below.

IMPORTANT:
- Use ONLY information explicitly present in the transcript.
- Never invent names, dates, deadlines, decisions, or responsibilities.
- Return ONLY valid JSON.
- Do not use markdown.
- Do not write explanations before or after the JSON.
- Use null when information is unavailable.

Return exactly this structure:

{{
    "summary": "...",
    "key_discussions": [
        {{
            "topic": "...",
            "discussion": "Provide a detailed explanation of what was discussed. Include the main ideas, questions, requirements, arguments, clarifications, and conclusions that are explicitly supported by the transcript. Do not merely repeat the topic.",
            "timestamp": "HH:MM:SS"
        }}
    ],
    "decisions": [
        {{
            "decision": "...",
            "speaker": "...",
            "timestamp": "HH:MM:SS"
        }}
    ],
    "action_items": [
        {{
            "task": "...",
            "assignee": null,
            "deadline": null,
            "timestamp": "HH:MM:SS"
        }}
    ],
    "next_steps": [],
    "important_points": [
        {{
            "point": "...",
            "timestamp": "HH:MM:SS"
        }}
    ]
}}

MEETING TRANSCRIPT:

{conversation}

"""
print("Sending transcript to Qwen...")

response = client.chat.completions.create(
    model="qwen3.5-4b-32k-fast",

    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ],

    max_tokens=3000
)


result = response.choices[0].message.content


if not result:
    raise RuntimeError("Qwen returned an empty response.")


print("\nAI response:")
print(result)
result = result.strip()

if result.startswith("```json"):
    result = result[7:]

elif result.startswith("```"):
    result = result[3:]


if result.endswith("```"):
    result = result[:-3]


result = result.strip()

try:
    raw_analysis = json.loads(result)

    validated_analysis = MeetingAnalysis.model_validate(raw_analysis)

    analysis = validated_analysis.model_dump()

except json.JSONDecodeError as error:

    print("\nQwen did not return valid JSON.")
    print("JSON error:", error)

    # Save the raw response so we can inspect it.
    with open(
        "analysis_raw.txt",
        "w",
        encoding="utf-8"
    ) as file:
        file.write(result)

    raise RuntimeError(
        "AI response could not be converted to JSON. "
        "Raw response saved to analysis_raw.txt"
    )

with open(
    output_file,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        analysis,
        file,
        indent=4,
        ensure_ascii=False
    )


print(f"Saved to: {output_file}")
