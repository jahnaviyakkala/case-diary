from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class CaseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    case_id: str
    title: str
    case_number: str
    court_name: str
    case_type: str
    status: str
    filed_date: str
    next_hearing_date: Optional[str] = None
    summary: str
    synthetic: bool = True


class TimelineItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hearing_no: int
    hearing_id: str
    hearing_date: str
    status: str
    purpose: str
    summary: str


class JudgeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    judge_id: str
    name: str
    designation: str


class ArgumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    argument_id: str
    hearing_id: str
    side: str
    text: str
    issue_tags: List[str] = []


class DirectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    direction_id: str
    hearing_id: str
    text: str
    issue_tags: List[str] = []


class AdjournmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    adjournment_id: str
    hearing_id: str
    reason: str
    requested_by: str


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    hearing_id: str
    name: str
    status_kind: str
    requested_by_submitted_by: str
    status: str
    resolved_hearing_id: Optional[str] = None


class ActionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action_id: str
    hearing_id: str
    description: str
    owner: str
    status: str
    due_date: Optional[str] = None
    resolved_hearing_id: Optional[str] = None


class OutcomeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    outcome_id: str
    hearing_id: str
    text: str


class HearingDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hearing_id: str
    case_id: str
    hearing_no: int
    hearing_date: str
    court_name: str
    judge: Optional[JudgeRead] = None
    status: str
    purpose: str
    summary: str
    next_hearing_date: Optional[str] = None
    arguments: List[ArgumentRead] = []
    directions: List[DirectionRead] = []
    adjournment: Optional[AdjournmentRead] = None
    documents: List[DocumentRead] = []
    action_items: List[ActionItemRead] = []
    outcome: Optional[OutcomeRead] = None


class SourceRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_id: str
    kind: str
    case_title: str
    hearing_no: Optional[int] = None
    hearing_date: Optional[str] = None
    text: str
    citation: str


class PendingItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: str
    item_type: str
    hearing_id: str
    hearing_no: int
    description: str
    owner_or_by: str
    status: str
    issue_tags: List[str] = []
