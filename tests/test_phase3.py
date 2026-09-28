import tempfile
import pytest
from sqlmodel import SQLModel, create_engine, Session, select

import services.case_service as cs
import services.seed as seed_module
from models.tables import Argument, CourtDirection, Hearing


@pytest.fixture(scope="module")
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    test_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        echo=False,
    )

    orig_seed_engine = seed_module.engine
    orig_cs_engine = cs.engine
    seed_module.engine = test_engine
    cs.engine = test_engine

    seed_module.seed_database(reset=True)

    yield test_engine

    seed_module.engine = orig_seed_engine
    cs.engine = orig_cs_engine


def test_reddy_hearings_count_and_contiguous(temp_db):
    timeline = cs.get_timeline("reddy-vs-state")
    assert len(timeline) == 15
    completed = [t for t in timeline if t.status == "completed"]
    scheduled = [t for t in timeline if t.status == "scheduled"]
    assert len(completed) == 14
    assert len(scheduled) == 1
    assert [t.hearing_no for t in timeline] == list(range(1, 16))


def test_hearing_8_date(temp_db):
    timeline = cs.get_timeline("reddy-vs-state")
    h8 = next(t for t in timeline if t.hearing_no == 8)
    assert h8.hearing_date == "2025-03-12"


def test_timeline_chronological_order(temp_db):
    timeline = cs.get_timeline("reddy-vs-state")
    dates = [t.hearing_date for t in timeline]
    assert dates == sorted(dates)


def test_get_source_record_resolution(temp_db):
    rec_case = cs.get_source_record("reddy-vs-state")
    assert rec_case is not None
    assert rec_case.kind == "case"

    rec_h8 = cs.get_source_record("REDDY-H08")
    assert rec_h8 is not None
    assert rec_h8.kind == "hearing"
    assert rec_h8.hearing_no == 8
    assert "Reddy vs. State" in rec_h8.citation

    rec_arg = cs.get_source_record("REDDY-H08-A01")
    assert rec_arg is not None
    assert rec_arg.kind == "argument"

    rec_dir = cs.get_source_record("REDDY-H08-D01")
    assert rec_dir is not None
    assert rec_dir.kind == "court_direction"

    rec_doc = cs.get_source_record("REDDY-H03-DOC01")
    assert rec_doc is not None
    assert rec_doc.kind == "document"

    rec_act = cs.get_source_record("REDDY-H08-ACT01")
    assert rec_act is not None
    assert rec_act.kind == "action_item"

    rec_fake = cs.get_source_record("NON-EXISTENT-ID-999")
    assert rec_fake is None


def test_get_pending_items_as_of_hearing_14(temp_db):
    pending = cs.get_pending_items("reddy-vs-state", 14)
    descriptions = [p.description for p in pending]

    assert any("Bank Statement — Account Ex. D-7" in d for d in descriptions)
    assert any("Prepare cross-examination points" in d for d in descriptions)


def test_certified_copy_pending_thread(temp_db):
    h3_detail = cs.get_hearing_detail("REDDY-H03")
    assert any("Bank Statement — Account Ex. D-7" in doc.name for doc in h3_detail.documents)

    h8_detail = cs.get_hearing_detail("REDDY-H08")
    assert any("certified-copy-pending" in d.issue_tags for d in h8_detail.directions)

    h11_detail = cs.get_hearing_detail("REDDY-H11")
    assert any(doc.status == "partial" for doc in h11_detail.documents)

    pending_h14 = cs.get_pending_items("reddy-vs-state", 14)
    assert any("Bank Statement — Account Ex. D-7" in p.description for p in pending_h14)


def test_issue_tags_distribution(temp_db):
    with Session(temp_db) as session:
        args = session.exec(select(Argument)).all()
        dirs = session.exec(select(CourtDirection)).all()

        tags_by_case = {}
        for arg in args:
            h = session.get(Hearing, arg.hearing_id)
            if h:
                tags_by_case.setdefault(h.case_id, set()).update(arg.issue_tags)
        for cd in dirs:
            h = session.get(Hearing, cd.hearing_id)
            if h:
                tags_by_case.setdefault(h.case_id, set()).update(cd.issue_tags)

        assert "electronic-evidence-certificate" in tags_by_case.get("reddy-vs-state", set())
        assert "electronic-evidence-certificate" in tags_by_case.get("nair-vs-state", set())

        assert "witness-absence-adjournment" in tags_by_case.get("reddy-vs-state", set())
        assert "witness-absence-adjournment" in tags_by_case.get("khan-vs-union", set())

        rao_tags = tags_by_case.get("rao-vs-property-corp", set())
        assert "electronic-evidence-certificate" not in rao_tags
        assert "witness-absence-adjournment" not in rao_tags


def test_all_cases_synthetic_flag(temp_db):
    cases = cs.list_cases()
    assert len(cases) == 4
    assert all(c.synthetic is True for c in cases)


def test_idempotent_seeding(temp_db):
    before_cases = len(cs.list_cases())
    before_h = len(cs.get_timeline("reddy-vs-state"))

    seed_module.seed_database(reset=False)

    after_cases = len(cs.list_cases())
    after_h = len(cs.get_timeline("reddy-vs-state"))

    assert before_cases == after_cases
    assert before_h == after_h


def test_validator_rejects_broken_fixtures():
    # Duplicate ID
    broken_dup = [
        {
            "case": {
                "case_id": "dup-case",
                "title": "Dup",
                "case_number": "1",
                "court_name": "Court",
                "case_type": "Civil",
                "status": "Ongoing",
                "filed_date": "2024-01-01",
                "summary": "Sum",
                "synthetic": True,
            },
            "hearings": [
                {
                    "hearing_id": "H1",
                    "case_id": "dup-case",
                    "hearing_no": 1,
                    "hearing_date": "2024-01-02",
                    "court_name": "Court",
                    "judge_id": "J1",
                    "status": "completed",
                    "purpose": "P1",
                    "summary": "S1",
                },
                {
                    "hearing_id": "H1",  # duplicate ID
                    "case_id": "dup-case",
                    "hearing_no": 2,
                    "hearing_date": "2024-01-03",
                    "court_name": "Court",
                    "judge_id": "J1",
                    "status": "completed",
                    "purpose": "P2",
                    "summary": "S2",
                },
            ],
            "judges": [{"judge_id": "J1", "name": "Judge 1", "designation": "Magistrate"}],
        }
    ]
    with pytest.raises(ValueError):
        seed_module.validate_data(broken_dup)

    # Bad FK
    broken_fk = [
        {
            "case": {
                "case_id": "fk-case",
                "title": "FK",
                "case_number": "1",
                "court_name": "Court",
                "case_type": "Civil",
                "status": "Ongoing",
                "filed_date": "2024-01-01",
                "summary": "Sum",
                "synthetic": True,
            },
            "hearings": [
                {
                    "hearing_id": "H1",
                    "case_id": "fk-case",
                    "hearing_no": 1,
                    "hearing_date": "2024-01-02",
                    "court_name": "Court",
                    "judge_id": "NON-EXISTENT-JUDGE",
                    "status": "completed",
                    "purpose": "P1",
                    "summary": "S1",
                }
            ],
            "judges": [],
        }
    ]
    with pytest.raises(ValueError):
        seed_module.validate_data(broken_fk)

    # Non-increasing dates
    broken_dates = [
        {
            "case": {
                "case_id": "date-case",
                "title": "Date",
                "case_number": "1",
                "court_name": "Court",
                "case_type": "Civil",
                "status": "Ongoing",
                "filed_date": "2024-01-01",
                "summary": "Sum",
                "synthetic": True,
            },
            "hearings": [
                {
                    "hearing_id": "H1",
                    "case_id": "date-case",
                    "hearing_no": 1,
                    "hearing_date": "2024-05-10",
                    "court_name": "Court",
                    "judge_id": "J1",
                    "status": "completed",
                    "purpose": "P1",
                    "summary": "S1",
                },
                {
                    "hearing_id": "H2",
                    "case_id": "date-case",
                    "hearing_no": 2,
                    "hearing_date": "2024-03-10",  # date goes backwards
                    "court_name": "Court",
                    "judge_id": "J1",
                    "status": "completed",
                    "purpose": "P2",
                    "summary": "S2",
                },
            ],
            "judges": [{"judge_id": "J1", "name": "Judge 1", "designation": "Magistrate"}],
        }
    ]
    with pytest.raises(ValueError):
        seed_module.validate_data(broken_dates)
