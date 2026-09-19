import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)


# -----------------------------
# Load transcript
# -----------------------------

with open("transcript.json", "r", encoding="utf-8") as file:
    transcript = json.load(file)


# -----------------------------
# PDF setup
# -----------------------------

output_file = "full_conversation.pdf"

doc = SimpleDocTemplate(
    output_file,
    pagesize=A4,
    rightMargin=18 * mm,
    leftMargin=18 * mm,
    topMargin=18 * mm,
    bottomMargin=18 * mm,
)


# -----------------------------
# Styles
# -----------------------------

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "TitleStyle",
    parent=styles["Title"],
    fontSize=22,
    leading=26,
    alignment=TA_CENTER,
    spaceAfter=8 * mm,
)

subtitle_style = ParagraphStyle(
    "SubtitleStyle",
    parent=styles["Normal"],
    fontSize=10,
    textColor=colors.grey,
    alignment=TA_CENTER,
    spaceAfter=12 * mm,
)

speaker_style = ParagraphStyle(
    "SpeakerStyle",
    parent=styles["Heading3"],
    fontSize=11,
    leading=14,
    spaceBefore=5 * mm,
    spaceAfter=2 * mm,
)

timestamp_style = ParagraphStyle(
    "TimestampStyle",
    parent=styles["Normal"],
    fontSize=8.5,
    textColor=colors.grey,
    spaceAfter=2 * mm,
)

conversation_style = ParagraphStyle(
    "ConversationStyle",
    parent=styles["Normal"],
    fontSize=10,
    leading=15,
    spaceAfter=5 * mm,
)


# -----------------------------
# Build PDF
# -----------------------------

story = []

story.append(
    Paragraph(
        "Full Meeting Conversation",
        title_style
    )
)

story.append(
    Paragraph(
        "Complete chronological transcript",
        subtitle_style
    )
)

story.append(Spacer(1, 4 * mm))


for entry in transcript:

    speaker = entry.get("speaker", "Unknown Speaker")
    start = entry.get("start", "")
    end = entry.get("end", "")
    text = entry.get("text", "")

    story.append(
        Paragraph(
            speaker,
            speaker_style
        )
    )

    story.append(
        Paragraph(
            f"{start} - {end}",
            timestamp_style
        )
    )

    story.append(
        Paragraph(
            text,
            conversation_style
        )
    )


# -----------------------------
# Generate
# -----------------------------

doc.build(story)

print(f"PDF created: {output_file}")