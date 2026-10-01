import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from rapidfuzz import fuzz

from storage import get_meeting_file

load_dotenv()

API_KEY = os.getenv("ASSEMBLYAI_API_KEY")


def load_chunks(meeting_id: str):
    chunks_file = get_meeting_file(meeting_id, "chunks.json")

    if not os.path.exists(chunks_file):
        raise FileNotFoundError(f"chunks.json was not found for meeting {meeting_id}.")

    with open(chunks_file, "r", encoding="utf-8") as file:
        return json.load(file)


def find_relevant_chunks(question, chunks):
    question_words = question.lower().split()
    scored_chunks = []

    for chunk in chunks:
        chunk_text = chunk.get("text", "").lower()
        if not chunk_text:
            continue

        score = 0
        for word in question_words:
            best_word_score = 0
            for text_word in chunk_text.split():
                similarity = fuzz.ratio(word, text_word)
                if similarity > best_word_score:
                    best_word_score = similarity
            score += best_word_score

        scored_chunks.append({"chunk": chunk, "score": score})

    scored_chunks.sort(key=lambda item: item["score"], reverse=True)
    return [item["chunk"] for item in scored_chunks[:3]]


def ask_meeting(meeting_id: str, question: str, history=None):
    if not API_KEY:
        raise RuntimeError("ASSEMBLYAI_API_KEY is not set.")

    client = OpenAI(
        api_key=API_KEY,
        base_url="https://llm-gateway.assemblyai.com/v1"
    )

    history_text = ""
    if history:
        history = history[-10:]
        for message in history:
            history_text += (
                f"{message['role']}: "
                f"{message['content']}\n"
            )

    chunks = load_chunks(meeting_id)

    if not chunks:
        return {
            "answer": "No meeting information is available.",
            "evidence": []
        }

    relevant_chunks = find_relevant_chunks(question, chunks)

    context_parts = []
    for chunk in relevant_chunks:
        context_parts.append(
            f"""
CHUNK {chunk.get("chunk_id")}

TIME:
{chunk.get("start")} - {chunk.get("end")}

TRANSCRIPT:
{chunk.get("text")}
"""
        )

    context = "\n".join(context_parts)

    prompt = f"""
You are a professional AI meeting assistant.

Answer the user's question using ONLY the
meeting transcript chunks provided below.
The conversation history is provided so you can understand
references such as "it", "that", "they", "this issue", etc.
IMPORTANT RULES:

1. Use only information contained in the provided chunks.
2. Never invent information.
3. Never use outside knowledge.
4. Understand the meaning of the user's question.
5. Correct obvious spelling mistakes internally.
   For example, "secuirty" may mean "security".
6. Do not mention spelling corrections unless necessary.
7. Combine information from multiple chunks when necessary.
8. If the provided chunks do not contain enough information,
   clearly say that the information was not found.
9. Do not claim that information is missing if the provided
   chunks actually contain relevant information.
10. Give a concise but complete answer.
11. Evidence must come directly from the provided chunks.
12. Return ONLY valid JSON.
13. Do not use markdown.
14. Do not add explanations outside the JSON.

Return exactly:

{{
    "answer": "...",
    "evidence": [
        {{
            "chunk_id": "...",
            "start": "...",
            "end": "...",
            "text": "..."
        }}
    ]
}}

CONVERSATION HISTORY:

{history_text}
USER QUESTION:

{question}

RELEVANT MEETING CHUNKS:

{context}
"""

    print("\nSending top 3 relevant chunks to Qwen...")

    response = client.chat.completions.create(
        model="qwen3.5-4b-32k-fast",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000
    )

    result = response.choices[0].message.content

    if not result:
        raise RuntimeError("Qwen returned an empty response.")

    result = result.strip()

    if result.startswith("```json"):
        result = result[7:]
    elif result.startswith("```"):
        result = result[3:]
    if result.endswith("```"):
        result = result[:-3]

    result = result.strip()

    try:
        return json.loads(result)
    except json.JSONDecodeError as error:
        print("\nInvalid JSON from Qwen:")
        print(result)

        raw_file = get_meeting_file(meeting_id, "qa_raw.txt")
        with open(raw_file, "w", encoding="utf-8") as file:
            file.write(result)

        raise RuntimeError(f"Qwen returned invalid JSON: {error}")