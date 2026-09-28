"""
Hindsight memory layer.

All reads and writes to long-term memory go through here. Every call is wrapped
so that a Hindsight outage never crashes the agent: the caller gets a
MemoryUnavailable and falls back to the local diary, and the UI shows that the
answer came from offline recall.
"""

import logging
import time
from datetime import datetime

from hindsight_client import Hindsight

from app.config import HINDSIGHT_API_KEY, HINDSIGHT_BANK, HINDSIGHT_URL

log = logging.getLogger("case-diary.memory")

BANK_MISSION = (
    "You are the long-term memory of Adv. Ananya Rao, a litigation advocate practising in Hyderabad courts. "
    "You remember every hearing across years: what each judge asked for, why matters were adjourned and by whom, "
    "what opposite counsel argued, what documents are due, and what was promised to clients."
)
RETAIN_MISSION = (
    "Extract concrete, checkable facts from court hearing notes: hearing number and date, who sought an adjournment "
    "and on what ground, directions and questions from the judge, documents due and from whom, rupee amounts and "
    "how they changed, witness status, promises made to the client, and lessons the advocate noted."
)
OBSERVATIONS_MISSION = (
    "Consolidate behavioural patterns that recur across cases: how each judge runs the court (tolerance for "
    "adjournments, preference for short written submissions, insistence on originals) and how each opposite counsel "
    "behaves (e.g. repeated adjournment requests and the grounds used). Track when a fact is later corrected."
)
DIRECTIVE = (
    "Only state facts that are present in memory. Always cite the case and hearing number a fact came from. "
    "Never predict the outcome of a case and never invent case law or citations."
)


class MemoryUnavailable(Exception):
    pass


class Memory:
    def __init__(self):
        self.bank = HINDSIGHT_BANK
        self._client = None
        self._down_until = 0.0
        self.last_error = None

    @property
    def client(self):
        if self._client is None:
            self._client = Hindsight(base_url=HINDSIGHT_URL, api_key=HINDSIGHT_API_KEY, timeout=90.0, max_attempts=2)
        return self._client

    def _call(self, fn, *args, **kwargs):
        # After a failure, skip Hindsight for 20s instead of making every request wait for a timeout.
        if time.time() < self._down_until:
            raise MemoryUnavailable(self.last_error or "Hindsight marked unavailable")
        try:
            result = fn(*args, **kwargs)
            self.last_error = None
            return result
        except Exception as exc:  # network errors, auth errors, 5xx from the server
            self.last_error = f"{type(exc).__name__}: {str(exc)[:200]}"
            self._down_until = time.time() + 20
            log.warning("Hindsight call failed: %s", self.last_error)
            raise MemoryUnavailable(self.last_error) from exc

    # -- setup ---------------------------------------------------------------

    def ensure_bank(self):
        try:
            self._call(
                self.client.create_bank, bank_id=self.bank, name="Case Diary — Adv. Ananya Rao",
                mission=BANK_MISSION, retain_mission=RETAIN_MISSION, observations_mission=OBSERVATIONS_MISSION,
                enable_observations=True, disposition_skepticism=4, disposition_literalism=4, disposition_empathy=2,
            )
        except MemoryUnavailable:
            if "already exists" not in (self.last_error or "").lower() and "409" not in (self.last_error or ""):
                raise
            self._down_until = 0
        try:
            existing = self._call(self.client.list_directives, bank_id=self.bank)
            if not any(d.name == "Grounded answers" for d in existing.items):
                self._call(self.client.create_directive, bank_id=self.bank, name="Grounded answers", content=DIRECTIVE)
        except MemoryUnavailable:
            self._down_until = 0  # directives are optional; do not block seeding over them

    def reset(self):
        try:
            self._call(self.client.delete_bank, bank_id=self.bank)
        except MemoryUnavailable:
            self._down_until = 0

    # -- write ---------------------------------------------------------------

    def retain(self, text, *, document_id, when, tags, metadata, context="court hearing note"):
        return self._call(
            self.client.retain, bank_id=self.bank, content=text, document_id=document_id,
            timestamp=datetime.fromisoformat(when), tags=tags, metadata=metadata, context=context,
        )

    def retain_batch(self, items):
        return self._call(self.client.retain_batch, bank_id=self.bank, items=items)

    # -- read ----------------------------------------------------------------

    def recall(self, query, *, tags=None, tags_match="any", types=None, budget="mid", max_tokens=4096):
        resp = self._call(
            self.client.recall, bank_id=self.bank, query=query, tags=tags, tags_match=tags_match,
            types=types, budget=budget, max_tokens=max_tokens,
        )
        facts = []
        for r in resp.results or []:
            meta = r.metadata or {}
            when = r.occurred_start or r.mentioned_at
            facts.append({
                "id": r.id,
                "text": r.text,
                "type": r.type or "world",
                "date": str(when)[:10] if when else None,
                "hearing_id": meta.get("hearing_id") or r.document_id,
                "case_id": meta.get("case_id"),
                "tags": r.tags or [],
            })
        return facts

    def reflect(self, query, *, tags=None, budget="mid"):
        resp = self._call(
            self.client.reflect, bank_id=self.bank, query=query, tags=tags, budget=budget, include_facts=True,
        )
        return resp.text or ""

    def stats(self):
        out = {}
        for kind in ("world", "experience", "observation"):
            try:
                out[kind] = self._call(self.client.list_memories, bank_id=self.bank, type=kind, limit=1).total
            except MemoryUnavailable:
                return None
        return out

    def healthy(self):
        try:
            self._call(self.client.get_version)
            return True
        except MemoryUnavailable:
            return False


memory = Memory()
