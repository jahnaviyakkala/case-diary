from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select

from models.db import engine
from models.tables import (
    Case,
    Hearing,
    Judge,
    Argument,
    CourtDirection,
    Adjournment,
    Document,
    ActionItem,
    Outcome,
    Party,
    Advocate,
)
from models.schemas import (
    CaseSummary,
    TimelineItem,
    HearingDetail,
    JudgeRead,
    ArgumentRead,
    DirectionRead,
    AdjournmentRead,
    DocumentRead,
    ActionItemRead,
    OutcomeRead,
    SourceRecord,
    PendingItem,
)


def _format_date(date_str: Optional[str]) -> str:
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        # Format as "12 Mar 2025" (removing leading zero on day if needed)
        day = dt.day
        month_abbr = dt.strftime("%b")
        year = dt.year
        return f"{day} {month_abbr} {year}"
    except Exception:
        return date_str


def list_cases(session: Optional[Session] = None) -> List[CaseSummary]:
    close_session = False
    if session is None:
        session = Session(engine)
        close_session = True

    try:
        cases = session.exec(select(Case)).all()
        return [CaseSummary.model_validate(c) for c in cases]
    finally:
        if close_session:
            session.close()


def get_case(case_id: str, session: Optional[Session] = None) -> Optional[CaseSummary]:
    close_session = False
    if session is None:
        session = Session(engine)
        close_session = True

    try:
        c = session.get(Case, case_id)
        if not c:
            return None
        return CaseSummary.model_validate(c)
    finally:
        if close_session:
            session.close()


def get_timeline(case_id: str, session: Optional[Session] = None) -> List[TimelineItem]:
    close_session = False
    if session is None:
        session = Session(engine)
        close_session = True

    try:
        statement = select(Hearing).where(Hearing.case_id == case_id).order_by(Hearing.hearing_no, Hearing.hearing_date)
        hearings = session.exec(statement).all()
        return [TimelineItem.model_validate(h) for h in hearings]
    finally:
        if close_session:
            session.close()


def get_hearing_detail(hearing_id: str, session: Optional[Session] = None) -> Optional[HearingDetail]:
    close_session = False
    if session is None:
        session = Session(engine)
        close_session = True

    try:
        h = session.get(Hearing, hearing_id)
        if not h:
            return None

        judge_obj = session.get(Judge, h.judge_id)
        judge_read = JudgeRead.model_validate(judge_obj) if judge_obj else None

        args = session.exec(select(Argument).where(Argument.hearing_id == hearing_id)).all()
        dirs = session.exec(select(CourtDirection).where(CourtDirection.hearing_id == hearing_id)).all()
        adj = session.exec(select(Adjournment).where(Adjournment.hearing_id == hearing_id)).first()
        docs = session.exec(select(Document).where(Document.hearing_id == hearing_id)).all()
        acts = session.exec(select(ActionItem).where(ActionItem.hearing_id == hearing_id)).all()
        out = session.exec(select(Outcome).where(Outcome.hearing_id == hearing_id)).first()

        return HearingDetail(
            hearing_id=h.hearing_id,
            case_id=h.case_id,
            hearing_no=h.hearing_no,
            hearing_date=h.hearing_date,
            court_name=h.court_name,
            judge=judge_read,
            status=h.status,
            purpose=h.purpose,
            summary=h.summary,
            next_hearing_date=h.next_hearing_date,
            arguments=[ArgumentRead.model_validate(a) for a in args],
            directions=[DirectionRead.model_validate(d) for d in dirs],
            adjournment=AdjournmentRead.model_validate(adj) if adj else None,
            documents=[DocumentRead.model_validate(doc) for doc in docs],
            action_items=[ActionItemRead.model_validate(act) for act in acts],
            outcome=OutcomeRead.model_validate(out) if out else None,
        )
    finally:
        if close_session:
            session.close()


def get_source_record(source_id: str, session: Optional[Session] = None) -> Optional[SourceRecord]:
    close_session = False
    if session is None:
        session = Session(engine)
        close_session = True

    try:
        # Check Case
        case_obj = session.get(Case, source_id)
        if case_obj:
            return SourceRecord(
                source_id=case_obj.case_id,
                kind="case",
                case_title=case_obj.title,
                hearing_no=None,
                hearing_date=None,
                text=case_obj.summary,
                citation=f"{case_obj.title} — Case Summary",
            )

        # Check Hearing
        hearing_obj = session.get(Hearing, source_id)
        if hearing_obj:
            c = session.get(Case, hearing_obj.case_id)
            c_title = c.title if c else hearing_obj.case_id
            formatted_date = _format_date(hearing_obj.hearing_date)
            return SourceRecord(
                source_id=hearing_obj.hearing_id,
                kind="hearing",
                case_title=c_title,
                hearing_no=hearing_obj.hearing_no,
                hearing_date=hearing_obj.hearing_date,
                text=f"{hearing_obj.purpose}: {hearing_obj.summary}",
                citation=f"{c_title} — Hearing {hearing_obj.hearing_no} — {formatted_date}",
            )

        # Helper for hearing-child records
        def _build_hearing_child_record(kind: str, hearing_id: str, text: str) -> Optional[SourceRecord]:
            h = session.get(Hearing, hearing_id)
            if not h:
                return None
            c = session.get(Case, h.case_id)
            c_title = c.title if c else h.case_id
            formatted_date = _format_date(h.hearing_date)
            return SourceRecord(
                source_id=source_id,
                kind=kind,
                case_title=c_title,
                hearing_no=h.hearing_no,
                hearing_date=h.hearing_date,
                text=text,
                citation=f"{c_title} — Hearing {h.hearing_no} — {formatted_date}",
            )

        # Check Argument
        arg_obj = session.get(Argument, source_id)
        if arg_obj:
            return _build_hearing_child_record("argument", arg_obj.hearing_id, f"[{arg_obj.side.capitalize()}] {arg_obj.text}")

        # Check CourtDirection
        dir_obj = session.get(CourtDirection, source_id)
        if dir_obj:
            return _build_hearing_child_record("court_direction", dir_obj.hearing_id, dir_obj.text)

        # Check Document
        doc_obj = session.get(Document, source_id)
        if doc_obj:
            return _build_hearing_child_record("document", doc_obj.hearing_id, f"{doc_obj.name} (Status: {doc_obj.status})")

        # Check ActionItem
        act_obj = session.get(ActionItem, source_id)
        if act_obj:
            return _build_hearing_child_record("action_item", act_obj.hearing_id, f"{act_obj.description} (Owner: {act_obj.owner}, Status: {act_obj.status})")

        # Check Adjournment
        adj_obj = session.get(Adjournment, source_id)
        if adj_obj:
            return _build_hearing_child_record("adjournment", adj_obj.hearing_id, f"Adjournment requested by {adj_obj.requested_by}: {adj_obj.reason}")

        # Check Outcome
        out_obj = session.get(Outcome, source_id)
        if out_obj:
            return _build_hearing_child_record("outcome", out_obj.hearing_id, out_obj.text)

        # Check Party
        party_obj = session.get(Party, source_id)
        if party_obj:
            return SourceRecord(
                source_id=party_obj.party_id,
                kind="party",
                case_title="General Party Record",
                hearing_no=None,
                hearing_date=None,
                text=f"{party_obj.name} ({party_obj.kind})",
                citation=f"{party_obj.name} — Party",
            )

        # Check Advocate
        adv_obj = session.get(Advocate, source_id)
        if adv_obj:
            return SourceRecord(
                source_id=adv_obj.advocate_id,
                kind="advocate",
                case_title="General Advocate Record",
                hearing_no=None,
                hearing_date=None,
                text=adv_obj.name,
                citation=f"{adv_obj.name} — Advocate",
            )

        # Check Judge
        judge_obj = session.get(Judge, source_id)
        if judge_obj:
            return SourceRecord(
                source_id=judge_obj.judge_id,
                kind="judge",
                case_title="General Judge Record",
                hearing_no=None,
                hearing_date=None,
                text=f"{judge_obj.name}, {judge_obj.designation}",
                citation=f"{judge_obj.name} — Judge",
            )

        return None
    finally:
        if close_session:
            session.close()


def get_pending_items(case_id: str, as_of_hearing_no: int, session: Optional[Session] = None) -> List[PendingItem]:
    close_session = False
    if session is None:
        session = Session(engine)
        close_session = True

    try:
        # All hearings for case up to as_of_hearing_no
        hearings = session.exec(
            select(Hearing).where(Hearing.case_id == case_id, Hearing.hearing_no <= as_of_hearing_no)
        ).all()

        hearing_no_map = {h.hearing_id: h.hearing_no for h in hearings}
        hearing_ids = list(hearing_no_map.keys())

        if not hearing_ids:
            return []

        pending_items: List[PendingItem] = []

        # Documents
        all_docs = session.exec(select(Document).where(Document.hearing_id.in_(hearing_ids))).all()
        for doc in all_docs:
            if doc.status in ["pending", "partial"]:
                # Check if resolved at or before as_of_hearing_no
                resolved_no = None
                if doc.resolved_hearing_id:
                    res_h = session.get(Hearing, doc.resolved_hearing_id)
                    if res_h:
                        resolved_no = res_h.hearing_no

                if resolved_no is None or resolved_no > as_of_hearing_no:
                    tags = ["certified-copy-pending"] if "certified" in doc.name.lower() or "bank statement" in doc.name.lower() else []
                    pending_items.append(
                        PendingItem(
                            item_id=doc.document_id,
                            item_type="document",
                            hearing_id=doc.hearing_id,
                            hearing_no=hearing_no_map[doc.hearing_id],
                            description=doc.name,
                            owner_or_by=doc.requested_by_submitted_by,
                            status=doc.status,
                            issue_tags=tags,
                        )
                    )

        # Action Items
        all_actions = session.exec(select(ActionItem).where(ActionItem.hearing_id.in_(hearing_ids))).all()
        for act in all_actions:
            resolved_no = None
            if act.resolved_hearing_id:
                res_h = session.get(Hearing, act.resolved_hearing_id)
                if res_h:
                    resolved_no = res_h.hearing_no

            is_open_as_of = act.status == "open" or (resolved_no is not None and resolved_no > as_of_hearing_no)
            if is_open_as_of:
                pending_items.append(
                    PendingItem(
                        item_id=act.action_id,
                        item_type="action_item",
                        hearing_id=act.hearing_id,
                        hearing_no=hearing_no_map[act.hearing_id],
                        description=act.description,
                        owner_or_by=act.owner,
                        status="open",
                        issue_tags=[],
                    )
                )

        return pending_items
    finally:
        if close_session:
            session.close()
