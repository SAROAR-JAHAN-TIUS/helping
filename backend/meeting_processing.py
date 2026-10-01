from chunker import create_chunks
from analyzer import analyze_meeting
from date_time import extract_calendar_events
from report_pdf import generate_report
from full_conversation import generate_full_conversation


def process_meeting(meeting_id: str):
    print(f"Processing meeting {meeting_id}...")

    print("1. Creating chunks...")
    create_chunks(meeting_id)

    print("2. Analyzing meeting...")
    analyze_meeting(meeting_id)

    print("3. Extracting calendar events...")
    extract_calendar_events(meeting_id)

    print("4. Generating meeting report...")
    generate_report(meeting_id)

    print("5. Generating full conversation PDF...")
    generate_full_conversation(meeting_id)

    print(f"Meeting {meeting_id} processing complete.")
