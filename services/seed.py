import argparse
import json
from pathlib import Path
from typing import List, Dict, Any
from sqlmodel import Session, SQLModel, select

from backend.config import settings
from models.db import engine, create_db
from models.tables import (
    Case,
    Party,
    CaseParty,
    Advocate,
    CaseAdvocate,
    Judge,
    Hearing,
    Argument,
    CourtDirection,
    Adjournment,
    Document,
    ActionItem,
    Outcome,
)


def load_json_files() -> List[Dict[str, Any]]:
    base_dir = Path(__file__).resolve().parent.parent / "data" / "synthetic"
    reddy_file = base_dir / "reddy_vs_state.json"
    other_file = base_dir / "other_cases.json"

    cases_data = []

    if reddy_file.exists():
        with open(reddy_file, "r", encoding="utf-8") as f:
            cases_data.append(json.load(f))

    if other_file.exists():
        with open(other_file, "r", encoding="utf-8") as f:
            other_data = json.load(f)
            if isinstance(other_data, list):
                cases_data.extend(other_data)
            else:
                cases_data.append(other_data)

    return cases_data


def validate_data(cases_data: List[Dict[str, Any]]):
    all_ids = set()

    for idx, case_bundle in enumerate(cases_data):
        case_info = case_bundle.get("case", {})
        case_id = case_info.get("case_id")

        if not case_id:
            raise ValueError(f"Case at index {idx} is missing 'case_id'.")

        if case_info.get("synthetic") is not True:
            raise ValueError(f"Case '{case_id}' is missing 'synthetic: true' flag.")

        if case_id in all_ids:
            raise ValueError(f"Duplicate case ID found: '{case_id}'.")
        all_ids.add(case_id)

        # Collect entity IDs
        parties = {p.get("party_id") for p in case_bundle.get("parties", [])}
        advocates = {a.get("advocate_id") for a in case_bundle.get("advocates", [])}
        judges = {j.get("judge_id") for j in case_bundle.get("judges", [])}

        for pid in parties:
            if pid in all_ids:
                raise ValueError(f"Duplicate party ID '{pid}' in case '{case_id}'.")
            all_ids.add(pid)

        for aid in advocates:
            if aid in all_ids:
                raise ValueError(f"Duplicate advocate ID '{aid}' in case '{case_id}'.")
            all_ids.add(aid)

        for jid in judges:
            if jid in all_ids:
                raise ValueError(f"Duplicate judge ID '{jid}' in case '{case_id}'.")
            all_ids.add(jid)

        # Check CaseParty and CaseAdvocate foreign keys
        for cp in case_bundle.get("case_parties", []):
            if cp.get("party_id") not in parties:
                raise ValueError(f"CaseParty in '{case_id}' references unknown party_id '{cp.get('party_id')}'.")

        for ca in case_bundle.get("case_advocates", []):
            if ca.get("advocate_id") not in advocates:
                raise ValueError(f"CaseAdvocate in '{case_id}' references unknown advocate_id '{ca.get('advocate_id')}'.")

        # Validate Hearings
        hearings = case_bundle.get("hearings", [])
        hearings_sorted = sorted(hearings, key=lambda x: x.get("hearing_no", 0))

        if len(hearings) == 0:
            raise ValueError(f"Case '{case_id}' has no hearings.")

        prev_date = ""
        expected_no = 1
        hearing_ids = set()

        for h in hearings_sorted:
            h_id = h.get("hearing_id")
            h_no = h.get("hearing_no")
            h_date = h.get("hearing_date")
            judge_id = h.get("judge_id")

            if not h_id:
                raise ValueError(f"Hearing in case '{case_id}' missing 'hearing_id'.")
            if h_id in all_ids:
                raise ValueError(f"Duplicate hearing ID found: '{h_id}'.")
            all_ids.add(h_id)
            hearing_ids.add(h_id)

            if h_no != expected_no:
                raise ValueError(f"Non-contiguous hearing_no in case '{case_id}': expected {expected_no}, got {h_no}.")
            expected_no += 1

            if h_date <= prev_date:
                raise ValueError(f"Hearing dates not strictly increasing in case '{case_id}': '{prev_date}' >= '{h_date}'.")
            prev_date = h_date

            if judge_id not in judges:
                raise ValueError(f"Hearing '{h_id}' references unknown judge_id '{judge_id}'.")

        # Validate child records against hearing_ids
        for arg in case_bundle.get("arguments", []):
            aid = arg.get("argument_id")
            hid = arg.get("hearing_id")
            if not aid or aid in all_ids:
                raise ValueError(f"Invalid or duplicate argument_id '{aid}'.")
            all_ids.add(aid)
            if hid not in hearing_ids:
                raise ValueError(f"Argument '{aid}' references unknown hearing_id '{hid}'.")

        for cd in case_bundle.get("court_directions", []):
            did = cd.get("direction_id")
            hid = cd.get("hearing_id")
            if not did or did in all_ids:
                raise ValueError(f"Invalid or duplicate direction_id '{did}'.")
            all_ids.add(did)
            if hid not in hearing_ids:
                raise ValueError(f"Direction '{did}' references unknown hearing_id '{hid}'.")

        for adj in case_bundle.get("adjournments", []):
            adj_id = adj.get("adjournment_id")
            hid = adj.get("hearing_id")
            if not adj_id or adj_id in all_ids:
                raise ValueError(f"Invalid or duplicate adjournment_id '{adj_id}'.")
            all_ids.add(adj_id)
            if hid not in hearing_ids:
                raise ValueError(f"Adjournment '{adj_id}' references unknown hearing_id '{hid}'.")

        for doc in case_bundle.get("documents", []):
            doc_id = doc.get("document_id")
            hid = doc.get("hearing_id")
            if not doc_id or doc_id in all_ids:
                raise ValueError(f"Invalid or duplicate document_id '{doc_id}'.")
            all_ids.add(doc_id)
            if hid not in hearing_ids:
                raise ValueError(f"Document '{doc_id}' references unknown hearing_id '{hid}'.")

        for act in case_bundle.get("action_items", []):
            act_id = act.get("action_id")
            hid = act.get("hearing_id")
            if not act_id or act_id in all_ids:
                raise ValueError(f"Invalid or duplicate action_id '{act_id}'.")
            all_ids.add(act_id)
            if hid not in hearing_ids:
                raise ValueError(f"ActionItem '{act_id}' references unknown hearing_id '{hid}'.")

        for out in case_bundle.get("outcomes", []):
            oid = out.get("outcome_id")
            hid = out.get("hearing_id")
            if not oid or oid in all_ids:
                raise ValueError(f"Invalid or duplicate outcome_id '{oid}'.")
            all_ids.add(oid)
            if hid not in hearing_ids:
                raise ValueError(f"Outcome '{oid}' references unknown hearing_id '{hid}'.")


def seed_database(reset: bool = False):
    cases_data = load_json_files()
    validate_data(cases_data)

    if reset:
        SQLModel.metadata.drop_all(engine)
        create_db(engine)

    stats = {
        "cases": 0,
        "hearings": 0,
        "arguments": 0,
        "directions": 0,
        "documents": 0,
        "action_items": 0,
    }

    with Session(engine) as session:
        for case_bundle in cases_data:
            c_data = case_bundle["case"]
            if not session.get(Case, c_data["case_id"]):
                session.add(Case(**c_data))
                stats["cases"] += 1

            for p in case_bundle.get("parties", []):
                if not session.get(Party, p["party_id"]):
                    session.add(Party(**p))

            for cp in case_bundle.get("case_parties", []):
                if not session.get(CaseParty, (cp["case_id"], cp["party_id"])):
                    session.add(CaseParty(**cp))

            for a in case_bundle.get("advocates", []):
                if not session.get(Advocate, a["advocate_id"]):
                    session.add(Advocate(**a))

            for ca in case_bundle.get("case_advocates", []):
                if not session.get(CaseAdvocate, (ca["case_id"], ca["advocate_id"])):
                    session.add(CaseAdvocate(**ca))

            for j in case_bundle.get("judges", []):
                if not session.get(Judge, j["judge_id"]):
                    session.add(Judge(**j))

            for h in case_bundle.get("hearings", []):
                if not session.get(Hearing, h["hearing_id"]):
                    session.add(Hearing(**h))
                    stats["hearings"] += 1

            for arg in case_bundle.get("arguments", []):
                if not session.get(Argument, arg["argument_id"]):
                    session.add(Argument(**arg))
                    stats["arguments"] += 1

            for cd in case_bundle.get("court_directions", []):
                if not session.get(CourtDirection, cd["direction_id"]):
                    session.add(CourtDirection(**cd))
                    stats["directions"] += 1

            for adj in case_bundle.get("adjournments", []):
                if not session.get(Adjournment, adj["adjournment_id"]):
                    session.add(Adjournment(**adj))

            for doc in case_bundle.get("documents", []):
                if not session.get(Document, doc["document_id"]):
                    session.add(Document(**doc))
                    stats["documents"] += 1

            for act in case_bundle.get("action_items", []):
                if not session.get(ActionItem, act["action_id"]):
                    session.add(ActionItem(**act))
                    stats["action_items"] += 1

            for out in case_bundle.get("outcomes", []):
                if not session.get(Outcome, out["outcome_id"]):
                    session.add(Outcome(**out))

        session.commit()

    print(
        f"Seeding completed successfully. Stats: {stats['cases']} cases, "
        f"{stats['hearings']} hearings, {stats['arguments']} arguments, "
        f"{stats['directions']} directions, {stats['documents']} documents, "
        f"{stats['action_items']} action items."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed database with synthetic case data.")
    parser.add_argument("--reset", action="store_true", help="Reset database tables before seeding.")
    args = parser.parse_args()
    seed_database(reset=args.reset)
