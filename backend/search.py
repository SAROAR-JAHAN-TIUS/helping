import re 
import json
from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()
API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
if not API_KEY:
    raise RuntimeError("ASSEMBLYAI_API_KEY is not set.")
client = OpenAI(
    api_key=API_KEY,
    base_url="https://llm-gateway.assemblyai.com/v1"
)
with open("meeting_analysis.json", "r", encoding="utf-8") as f:
    meeting_analysis = json.load(f)
STOP_WORDS = {
    "what", "did", "they", "the", "about",
    "is", "are", "a", "an", "to", "of",
    "in", "on", "for", "was", "were",
    "who", "when", "where", "how",
    "do", "does", "did", "and"
}

def extract_keywords(text):
   text = text.lower()
   words = re.findall(r'\b\w+\b', text)
   keywords = [word 
               for word in words 
               if word not in STOP_WORDS]
   return keywords

def calculate_keyword_frequency(chunk, question):

    question_words = extract_keywords(question)

    chunk_text = chunk["text"].lower()

    score = 0

    # 1. Individual keyword matches
    for word in question_words:
        if word in chunk_text:
            score += 1

    # 2. Exact phrase match
    question_clean = " ".join(question_words)

    if question_clean in chunk_text:
        score += 3

    return score
def find_best_entry(question, entries):

    question_keywords = extract_keywords(question)

    best_entry = None
    best_score = 0

    for entry in entries:

        entry_words = set(
            re.findall(
                r"\b\w+\b",
                entry["text"].lower()
            )
        )

        score = 0

        for keyword in question_keywords:

            if keyword in entry_words:
                score += 1

        if score > best_score:
            best_score = score
            best_entry = entry

    return best_entry
with open("chunks.json", "r", encoding="utf-8") as file:
    chunks = json.load(file)


question = input("Ask about the meeting: ")
question_lower = question.lower()


if (
    "action item" in question_lower
    or "actions items" in question_lower
    or "tasks" in question_lower
    or "things to do" in question_lower
):
    action_items = meeting_analysis.get("action_items", [])
    if not action_items:
        print("\nAI Answer:")
        print("No action items were identified in the meeting analysis.")
        exit()

    print("\nAI Answer:")

    for i, item in enumerate(action_items, start=1):
        print(f"\n{i}. {item['task']}")

        if item.get("assignee"):
            print(f"   Assignee: {item['assignee']}")

        if item.get("deadline"):
            print(f"   Deadline: {item['deadline']}")

        print(f"   Timestamp: {item['timestamp']}")

    exit()

        
if "decision" in question_lower:
    decisions = meeting_analysis.get("decisions", [])

    if not decisions:
        print("\nAI Answer:")
        print("No decisions were identified in the meeting analysis.")
        exit()

    print("\nAI Answer:")

    for i, item in enumerate(decisions, start=1):
        print(f"\n{i}. {item['decision']}")

        if item.get("speaker"):
            print(f"   Speaker: {item['speaker']}")

        print(f"   Timestamp: {item['timestamp']}")

    exit()
# -----------------------------------
# NEXT STEPS
# -----------------------------------

if "next step" in question_lower:
    next_steps = meeting_analysis.get("next_steps", [])

    if not next_steps:
        print("\nAI Answer:")
        print("No next steps were identified in the meeting analysis.")
        exit()

    print("\nAI Answer:")

    for i, step in enumerate(next_steps, start=1):
        print(f"\n{i}. {step}")

    exit()
results = []
for chunk in chunks:

    score = calculate_keyword_frequency(
        chunk,
        question
    )

    results.append({
        "score": score,
        "chunk": chunk
    })

results.sort(key=lambda x: x["score"], reverse=True)
top_chunks = results[:3]
relevant_entries = []

for result in top_chunks:
    relevant_entries.extend(
        result["chunk"]["entries"]
    )
context = "\n\n".join(
    result["chunk"]["text"]
    for result in top_chunks
)    
prompt = f"""
You are an AI meeting assistant.

Your job is to answer questions about the meeting using ONLY the provided
meeting transcript.

IMPORTANT RULES:

1. Never invent information.
2. Never assume something happened unless the transcript supports it.
3. If the transcript does not contain enough information to answer the question,
   say:
   "I couldn't find that information in the meeting."
4. Distinguish between:
   - Discussion: something people talked about.
   - Decision: something the participants agreed to do or accepted.
   - Action item: a specific task someone is expected to perform.
   - Next step: something that should happen after the meeting.
5. A statement is an action item only when the transcript indicates that
   someone is expected to do something.
6. Do not turn general discussion into an action item.
7. Do not invent an assignee or deadline.
8. If the transcript contains multiple relevant points, include them.
9. Evidence must be copied exactly from the provided transcript.
10. Do not add quotation marks around the evidence.
11. The evidence must come from one transcript entry.
12. Return only valid JSON.
An action item must represent a specific task that someone is expected
to perform.

Do NOT classify these as action items:
- general discussion
- suggestions
- ideas
- proposals
- decisions without a specific task
- statements describing what the team discussed

Only call something an action item when the transcript supports an actual
task or responsibility.
Return this structure:

{{
    "answer": "Your concise answer.",
    "evidence": "Exact supporting sentence from the transcript."
}}

If no relevant information exists:

{{
    "answer": "I couldn't find that information in the meeting.",
    "evidence": ""
}}

User question:
{question}

Relevant meeting transcript:
{context}
"""

response = client.chat.completions.create(
    model="qwen3.5-4b-32k-fast",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ],
    max_tokens=1000

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
# print("\nRAW LLM RESPONSE:")
# print(result)
# print("\nEND RAW RESPONSE\n")
data = json.loads(result)

ai_answer = data["answer"]
evidence = data["evidence"]

evidence_entry = None

for entry in relevant_entries:
    if evidence.strip() in entry["text"].strip():
        evidence_entry = entry
        break


print("\nAI Answer:")
print(ai_answer)

print("\nEvidence:")
print(evidence)

if evidence_entry:
    print(
        f"\nTimestamp: {evidence_entry['start']}"
    )
else:
    print("\nTimestamp: Not found")