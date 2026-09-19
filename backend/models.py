from typing import Optional
from pydantic import BaseModel


class KeyDiscussion(BaseModel):
    topic: str
    discussion: str
    timestamp: str


class Decision(BaseModel):
    decision: str
    speaker: str
    timestamp: str


class ActionItem(BaseModel):
    task: str
    assignee: Optional[str] = None
    deadline: Optional[str] = None
    timestamp: str


class ImportantPoint(BaseModel):
    point: str
    timestamp: str


class MeetingAnalysis(BaseModel):
    summary: str
    key_discussions: list[KeyDiscussion]
    decisions: list[Decision]
    action_items: list[ActionItem]
    next_steps: list[str]
    important_points: list[ImportantPoint]