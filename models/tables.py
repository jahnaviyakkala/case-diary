from typing import List, Optional
from sqlmodel import SQLModel, Field, Column, JSON


class Case(SQLModel, table=True):
    case_id: str = Field(primary_key=True)
    title: str
    case_number: str
    court_name: str
    case_type: str
    status: str
    filed_date: str
    next_hearing_date: Optional[str] = None
    summary: str
    synthetic: bool = Field(default=True)


class Party(SQLModel, table=True):
    party_id: str = Field(primary_key=True)
    name: str
    kind: str


class CaseParty(SQLModel, table=True):
    case_id: str = Field(foreign_key="case.case_id", primary_key=True, index=True)
    party_id: str = Field(foreign_key="party.party_id", primary_key=True, index=True)
    role: str


class Advocate(SQLModel, table=True):
    advocate_id: str = Field(primary_key=True)
    name: str


class CaseAdvocate(SQLModel, table=True):
    case_id: str = Field(foreign_key="case.case_id", primary_key=True, index=True)
    advocate_id: str = Field(foreign_key="advocate.advocate_id", primary_key=True, index=True)
    side: str
    is_our_client_side: bool = Field(default=False)


class Judge(SQLModel, table=True):
    judge_id: str = Field(primary_key=True)
    name: str
    designation: str


class Hearing(SQLModel, table=True):
    hearing_id: str = Field(primary_key=True)
    case_id: str = Field(foreign_key="case.case_id", index=True)
    hearing_no: int = Field(index=True)
    hearing_date: str
    court_name: str
    judge_id: str = Field(foreign_key="judge.judge_id", index=True)
    status: str
    purpose: str
    summary: str
    next_hearing_date: Optional[str] = None


class Argument(SQLModel, table=True):
    argument_id: str = Field(primary_key=True)
    hearing_id: str = Field(foreign_key="hearing.hearing_id", index=True)
    side: str
    text: str
    issue_tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))


class CourtDirection(SQLModel, table=True):
    direction_id: str = Field(primary_key=True)
    hearing_id: str = Field(foreign_key="hearing.hearing_id", index=True)
    text: str
    issue_tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))


class Adjournment(SQLModel, table=True):
    adjournment_id: str = Field(primary_key=True)
    hearing_id: str = Field(foreign_key="hearing.hearing_id", unique=True, index=True)
    reason: str
    requested_by: str


class Document(SQLModel, table=True):
    document_id: str = Field(primary_key=True)
    hearing_id: str = Field(foreign_key="hearing.hearing_id", index=True)
    name: str
    status_kind: str
    requested_by_submitted_by: str
    status: str
    resolved_hearing_id: Optional[str] = Field(default=None, foreign_key="hearing.hearing_id")


class ActionItem(SQLModel, table=True):
    action_id: str = Field(primary_key=True)
    hearing_id: str = Field(foreign_key="hearing.hearing_id", index=True)
    description: str
    owner: str
    status: str
    due_date: Optional[str] = None
    resolved_hearing_id: Optional[str] = Field(default=None, foreign_key="hearing.hearing_id")


class Outcome(SQLModel, table=True):
    outcome_id: str = Field(primary_key=True)
    hearing_id: str = Field(foreign_key="hearing.hearing_id", unique=True, index=True)
    text: str
