

from chunker import create_chunks
from analyzer import analyze_meeting
from date_time import extract_calendar_events
from report_pdf import generate_report
from full_conversation import generate_full_conversation
def process_meeting():
    print("Processing meeting...")

    create_chunks()

    print("2. Analyzing meeting...")
    analyze_meeting()

    print("3. Extracting calendar events...")
    extract_calendar_events()
    print("4. Generating meeting report...")
     
    generate_report()
    print("5. Generating full conversation PDF...")
        
    generate_full_conversation()
    print("Meeting processing complete.")

if __name__ == "__main__":
    process_meeting()
