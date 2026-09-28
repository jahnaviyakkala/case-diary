"""
Runs without Hindsight or an LLM key: these tests cover the parts that must keep
working when both are down.

    python -m pytest -q
"""

import os

os.environ["HINDSIGHT_URL"] = "http://127.0.0.1:9"  # nothing listens here: forces the offline path
for _k in ("LLM_API_KEY", "LLM_API_KEY_2", "LLM_API_KEY_3", "GROQ_API_KEY"):
    os.environ[_k] = ""

from fastapi.testclient import TestClient  # noqa: E402

from app import agent, llm  # noqa: E402
from app.diary import diary  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def test_dataset_is_substantial_and_consistent():
    assert len(diary.cases) >= 50 and len(diary.hearings) >= 500
    for cid in diary.cases:
        dates = [h["date"] for h in diary.case_hearings(cid)]
        assert dates == sorted(dates)


def test_flagship_case_is_tomorrow():
    reddy = diary.cases["reddy-vs-state"]
    assert diary.cause_list(1)[0]["id"] == "reddy-vs-state"
    assert reddy["next_date"] > diary.today.isoformat()


def test_case_resolution_from_natural_language():
    assert diary.find_case("Prep me for tomorrow's hearing in Reddy vs. State")[0]["id"] == "reddy-vs-state"
    assert diary.find_case("C.C. 1187")[0]["id"] == "reddy-vs-state"
    assert diary.find_case("qwertyuiop")[0] is None


def test_brief_survives_hindsight_and_llm_outage():
    b = agent.brief("reddy-vs-state")
    assert b["memory_source"] == "offline"
    assert b["composer"] == "template"
    assert b["facts"], "offline recall should still surface diary facts"
    # the cross-case adjournment pattern is still found: 3 of Chary's last 4 matters before this bench
    assert b["pattern"]["adjourned_matters"] == 3 and b["pattern"]["total_matters"] == 4


def test_memory_depth_hides_later_hearings():
    b = agent.brief("reddy-vs-state", as_of_no=5)
    nos = [f["source"]["no"] for f in b["facts"] if f["source"] and f["source"]["case_id"] == "reddy-vs-state"]
    assert nos and max(nos) <= 5


def test_invented_citations_are_dropped():
    out = agent._clean_cites({"bench_expects": [{"text": "real", "cites": ["F1"]}, {"text": "made up", "cites": ["F99"]}]},
                             {"F1"})
    assert [x["text"] for x in out["bench_expects"]] == ["real"]


def test_llm_json_parsing_is_tolerant():
    assert llm._extract_json('<think>hmm</think>```json\n{"a": 1}\n```') == {"a": 1}
    assert llm._extract_json('Sure! Here it is: {"a": 2} hope that helps') == {"a": 2}


def test_api_endpoints():
    assert client.get("/api/health").json()["hindsight"]["ok"] is False
    assert client.get("/api/docket").json()["upcoming"]
    assert client.get("/api/cases/nope").status_code == 404
    assert client.post("/api/ask", json={"question": "Has Chary sought adjournments?"}).status_code == 200
    assert client.get("/api/people/judge/J-KVR").json()["stats"]["cases"] >= 5
