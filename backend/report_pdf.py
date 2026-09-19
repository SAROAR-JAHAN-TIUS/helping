import json

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


INPUT_FILE = "meeting_analysis.json"
OUTPUT_FILE = "meeting_report.pdf"




with open(INPUT_FILE, "r", encoding="utf-8") as file:
    analysis = json.load(file)




doc = SimpleDocTemplate(
    OUTPUT_FILE,
    pagesize=A4,
    rightMargin=18 * mm,
    leftMargin=18 * mm,
    topMargin=18 * mm,
    bottomMargin=18 * mm,
)


styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "Title",
    parent=styles["Title"],
    alignment=TA_CENTER,
    fontSize=22,
    spaceAfter=10,
)

section_style = ParagraphStyle(
    "Section",
    parent=styles["Heading2"],
    fontSize=15,
    spaceBefore=14,
    spaceAfter=8,
)

subsection_style = ParagraphStyle(
    "Subsection",
    parent=styles["Heading3"],
    fontSize=11,
    spaceBefore=8,
    spaceAfter=4,
)

body_style = ParagraphStyle(
    "Body",
    parent=styles["BodyText"],
    fontSize=10,
    leading=15,
    spaceAfter=6,
)

small_style = ParagraphStyle(
    "Small",
    parent=styles["BodyText"],
    fontSize=8,
    leading=11,
)



story = []


story.append(
    Paragraph(
        "Meeting Report",
        title_style
    )
)

story.append(
    Paragraph(
        "AI-generated meeting analysis",
        small_style
    )
)

story.append(Spacer(1, 15))



story.append(
    Paragraph(
        "Executive Summary",
        section_style
    )
)

summary = analysis.get("summary", "")

story.append(
    Paragraph(
        summary,
        body_style
    )
)




story.append(
    Paragraph(
        "Key Discussions",
        section_style
    )
)

discussions = analysis.get("key_discussions", [])

if discussions:

    for discussion in discussions:

        topic = discussion.get("topic", "")
        text = discussion.get("discussion", "")
        timestamp = discussion.get("timestamp", "")

        story.append(
            Paragraph(
                topic,
                subsection_style
            )
        )

        story.append(
            Paragraph(
                text,
                body_style
            )
        )

        story.append(
            Paragraph(
                f"<b>Timestamp:</b> {timestamp}",
                small_style
            )
        )

else:

    story.append(
        Paragraph(
            "No key discussions were identified.",
            body_style
        )
    )




story.append(
    Paragraph(
        "Decisions",
        section_style
    )
)

decisions = analysis.get("decisions", [])

if decisions:

    data = [
        [
            Paragraph("<b>Decision</b>", small_style),
            Paragraph("<b>Speaker</b>", small_style),
            Paragraph("<b>Time</b>", small_style),
        ]
    ]

    for item in decisions:

        data.append(
            [
                Paragraph(
                    item.get("decision", ""),
                    small_style
                ),
                Paragraph(
                    item.get("speaker", ""),
                    small_style
                ),
                Paragraph(
                    item.get("timestamp", ""),
                    small_style
                ),
            ]
        )

    table = Table(
        data,
        colWidths=[
            105 * mm,
            35 * mm,
            20 * mm,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    story.append(table)

else:

    story.append(
        Paragraph(
            "No decisions were identified.",
            body_style
        )
    )


story.append(
    Paragraph(
        "Action Items",
        section_style
    )
)

actions = analysis.get("action_items", [])

if actions:

    data = [
        [
            Paragraph("<b>Task</b>", small_style),
            Paragraph("<b>Assignee</b>", small_style),
            Paragraph("<b>Deadline</b>", small_style),
            Paragraph("<b>Time</b>", small_style),
        ]
    ]

    for item in actions:

        assignee = item.get("assignee") or "Not specified"
        deadline = item.get("deadline") or "Not specified"

        data.append(
            [
                Paragraph(
                    item.get("task", ""),
                    small_style
                ),
                Paragraph(
                    assignee,
                    small_style
                ),
                Paragraph(
                    deadline,
                    small_style
                ),
                Paragraph(
                    item.get("timestamp", ""),
                    small_style
                ),
            ]
        )

    table = Table(
        data,
        colWidths=[
            75 * mm,
            35 * mm,
            35 * mm,
            15 * mm,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    story.append(table)

else:

    story.append(
        Paragraph(
            "No action items were identified.",
            body_style
        )
    )


story.append(
    Paragraph(
        "Next Steps",
        section_style
    )
)

next_steps = analysis.get("next_steps", [])

if next_steps:

    for index, step in enumerate(next_steps, start=1):

        story.append(
            Paragraph(
                f"{index}. {step}",
                body_style
            )
        )

else:

    story.append(
        Paragraph(
            "No next steps were identified.",
            body_style
        )
    )



story.append(
    Paragraph(
        "Important Points",
        section_style
    )
)

important_points = analysis.get("important_points", [])

if important_points:

    for item in important_points:

        story.append(
            Paragraph(
                f"<b>{item.get('timestamp', '')}</b> "
                f"{item.get('point', '')}",
                body_style
            )
        )

else:

    story.append(
        Paragraph(
            "No additional important points were identified.",
            body_style
        )
    )


doc.build(story)

print(f"Meeting report created: {OUTPUT_FILE}")