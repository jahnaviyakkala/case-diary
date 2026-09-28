import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import agent
from app.config import ROOT
from app.diary import diary

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
app = FastAPI(title="Case Diary", version="1.0")
WEB = ROOT / "web"


@app.exception_handler(Exception)
async def unhandled(_, exc):
    logging.getLogger("case-diary").exception("Unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Something went wrong on our side. The diary is intact; try again."})


def _case_or_404(case_id):
    if case_id not in diary.cases:
        raise HTTPException(404, f"No case with id '{case_id}'")
    return diary.cases[case_id]


@app.get("/api/health")
def health():
    return agent.health()


@app.get("/api/docket")
def docket():
    upcoming = [diary.case_view(c["id"]) for c in diary.cause_list(7)]
    return {"today": diary.today.isoformat(), "advocate": diary.advocate, "upcoming": upcoming,
            "cases": sorted((diary.case_view(c) for c in diary.cases), key=lambda c: c["title"]),
            "totals": {"cases": len(diary.cases), "hearings": len(diary.hearings)}}


@app.get("/api/resolve")
def resolve(q: str):
    case, suggestions = diary.find_case(q)
    return {"case": case and case["id"], "suggestions": [{"id": c["id"], "title": c["title"]} for c in suggestions]}


@app.get("/api/cases/{case_id}")
def case_detail(case_id: str):
    _case_or_404(case_id)
    return {"case": diary.case_view(case_id),
            "hearings": [{**h, "judge_name": diary.judges.get(h["judge"], {}).get("name")}
                         for h in diary.case_hearings(case_id)]}


@app.get("/api/cases/{case_id}/brief")
def case_brief(case_id: str, memory: bool = True, as_of: int | None = None, fresh: bool = False):
    _case_or_404(case_id)
    return agent.brief(case_id, use_memory=memory, as_of_no=as_of, force=fresh)


class Ask(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    case_id: str | None = None


@app.post("/api/ask")
def ask(body: Ask):
    return agent.ask(body.question, body.case_id)


class Log(BaseModel):
    note: str = Field(min_length=10, max_length=4000)
    date: str | None = None


@app.post("/api/cases/{case_id}/hearings")
def log_hearing(case_id: str, body: Log):
    _case_or_404(case_id)
    return agent.log_hearing(case_id, body.note, body.date)


@app.get("/api/people")
def people():
    def count(key, pid):
        return sum(1 for h in diary.hearings.values() if h[key] == pid)
    return {
        "judges": [{"id": k, **v, "court_name": diary.courts[v["court"]], "hearings": count("judge", k)}
                   for k, v in diary.judges.items()],
        "counsel": [{"id": k, **v, "hearings": count("counsel", k)} for k, v in diary.counsel.items()],
    }


@app.get("/api/people/{kind}/{pid}")
def person(kind: str, pid: str):
    if kind not in ("judge", "counsel") or pid not in (diary.judges if kind == "judge" else diary.counsel):
        raise HTTPException(404, "Unknown person")
    return agent.profile(kind, pid)


app.mount("/static", StaticFiles(directory=WEB), name="static")


@app.get("/")
def index():
    return FileResponse(WEB / "index.html")
