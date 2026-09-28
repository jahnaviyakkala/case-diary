<div align="center">

<img src="docs/screens/mark.svg" width="56" alt="">

# Case Diary

**A hearing-preparation agent for Indian litigation lawyers that remembers every hearing, every bench and every opposite counsel, across years and across cases.**

<p>
<img src="https://img.shields.io/badge/memory-Hindsight-7A1F1F?style=flat-square" alt="Hindsight">
<img src="https://img.shields.io/badge/LLM-Groq%20·%20gpt--oss--120b-2D5A45?style=flat-square" alt="Groq">
<img src="https://img.shields.io/badge/python-3.10+-1D1B17?style=flat-square&logo=python&logoColor=F4F0E7" alt="Python">
<img src="https://img.shields.io/badge/FastAPI-backend-1D1B17?style=flat-square&logo=fastapi&logoColor=F4F0E7" alt="FastAPI">
<img src="https://img.shields.io/badge/frontend-no%20build%20step-9A5B12?style=flat-square" alt="No build">
<img src="https://img.shields.io/badge/data-52%20cases%20·%20505%20hearings-7D776B?style=flat-square" alt="Data">
</p>

<img src="docs/screens/docket.png" width="880" alt="Case Diary docket view">

</div>

---

## The problem

India has over **5 crore pending cases**. A criminal trial in a Hyderabad magistrate's court routinely runs for four or five years and fifteen or more hearings, most of them adjourned. A mid-level advocate carries 80 to 200 live matters, and the only memory of each is a paper diary plus their own recall.

The night before a hearing, that advocate needs to know:

- what happened last time, and what the judge asked for
- which documents are still pending, and from whom
- what they promised the client
- whether a figure or a witness's position has **changed** since it was first recorded
- how this judge runs the court, and how this opposite counsel behaves, **across every other matter**, not just this one

None of this is legal research. It is memory. A stateless LLM cannot help with it, however capable, because it has never seen the hearings.

## What Case Diary does

> **"Prep me for tomorrow's hearing in Reddy vs. State."**

The agent recalls the case's 14 hearings from Hindsight, looks across the advocate's other matters before the same bench, and writes a brief in which **every line cites the hearing it came from**:

- **Last time.** At H14, PW-3's cross was partly done, and the judge gave the prosecution a *last chance* to produce the certified HDFC statement.
- **The bench expects.** State whether the defence disputes the signature on Ex. P-4, and keep any written note to five pages. This judge refused a 44-page note at H12.
- **Watch out.** APP B. Narasimha Chary sought an adjournment in **3 of his last 4 matters** before Sri K. Venkateswara Rao, mostly on medical grounds. In this case he did so at H5, H11 and H13, and the court imposed ₹2,000 costs.
- **Be ready to say.** A one-line, pre-emptive response pointing the court to its own order at H13.
- **Changed since first recorded.** The charge says ₹42,00,000. PW-1 said in chief (H7) that she paid ₹38,50,000.
- **Promised to the client.** The passport petition for his daughter's wedding in Dubai (H9, H14) is still open.

Flip the **Memory** switch off and the same request produces what any chatbot would produce: generic advice about cross-examination.

<div align="center"><img src="docs/screens/brief.png" width="880" alt="A memory-backed hearing brief with citations"></div>

<div align="center"><img src="docs/screens/timeline.png" width="880" alt="Hearing timeline"></div>

## How Hindsight memory is used

Memory is the core of the product, not a feature added to it. The brief is written **only** from what Hindsight recalls. The local diary exists to render hearings into memory and to serve as a fallback.

| Hindsight capability | Where Case Diary uses it |
|---|---|
| **`retain`** with `document_id`, `timestamp`, `tags`, `metadata` | Every hearing becomes a dated memory, tagged `case:`, `judge:`, `counsel:` and `court:`. The `document_id` is the hearing id, so re-seeding is idempotent. |
| **Bank `mission`, `retain_mission`, `observations_mission`** | Tell Hindsight to extract adjournment grounds, directions, rupee amounts, witness status and client promises, and to consolidate *behavioural patterns* of judges and counsel. |
| **`recall`** with tag scoping, run as six parallel lanes | *This case* (history, directions, promises). *Opposite counsel* across all their matters. *The bench* across all matters. Each lane is its own recall with its own tags and budget. |
| **Observations** (`types=["observation"]`) | Patterns Hindsight learned by itself across hearings, shown as **learned** in the memory rail and on the Bench & Bar profiles. |
| **Directives** | A hard rule on the bank: only state facts present in memory, always cite the hearing, never predict outcomes. |
| **Temporal facts** (`occurred_start`, `mentioned_at`) | Facts are ordered newest first, so the newer version wins when two conflict, and the **memory depth** slider can rewind the brief to any earlier hearing. |

### The learning curve, made visible

The brief page has a **"Memory up to hearing"** slider. Drag it back to H3 and the brief is thin: a few directions and no pattern. At H8 the amount discrepancy appears. At H14 the adjournment pattern, the bench's dislike of long notes and the open client promises are all there. Every **Log a hearing** adds to it.

### Time and contradiction

Facts change: a witness revises a figure, a pending document finally arrives, a client changes an instruction. When a new hearing note is logged:

1. The note is compared against everything memory holds for that case.
2. Anything that **corrects, updates or contradicts** an earlier fact is shown as *before → after*, with the hearing where the old fact was recorded.
3. The hearing is retained, and **each correction is retained as its own newer, dated memory** ("as of H15, X is now Y; this supersedes Z recorded at H7"). The old fact is superseded, not silently erased, which is how a lawyer thinks about a record.

Try it with the sample note on the Reddy case. It reports the amount changing from ₹38,50,000 (H7) to ₹40,00,000, and the certified statement moving from *pending* to *produced*.

## When things go wrong

A tool a lawyer relies on at 11 pm cannot show a stack trace. Every dependency has a defined failure mode.

| What fails | What the user sees | How |
|---|---|---|
| **Hindsight unreachable** | The brief still appears, with an amber *"answered from the local diary"* banner. | Recall falls back to keyword search over the diary, split into sentence-level facts. A 20-second circuit breaker stops every request from waiting on a timeout. |
| **Hindsight down while logging a hearing** | *"Saved · 2 queued, will sync automatically."* | The note is saved locally and queued in `data/runtime/retain_queue.json`. The health check flushes the queue when memory returns. |
| **LLM rate-limited (Groq 429)** | Nothing visible. | Up to three keys rotate round-robin, so their per-minute limits add up. A rate-limited key rests for exactly as long as Groq's `retry-after` header says, while the others keep serving. If all are resting, the call waits (bounded) and then tries the fallback model (`openai/gpt-oss-20b`). |
| **LLM returns broken JSON or `<think>` noise** | Nothing visible. | Tolerant parsing, then one re-ask for strict JSON. |
| **LLM completely unavailable** | The brief shows recalled facts under the same headings, with a banner. | A template composer that invents nothing. |
| **LLM cites a fact that does not exist** | The claim is dropped. | Citations are validated against the recalled fact ids before rendering. |
| **Ambiguous case name** ("prep me for Sharma") | *"Which matter did you mean?"* with suggestions. | Fuzzy resolution with a confidence threshold. |
| **Seeding interrupted halfway** | Run the same command again. | Progress is checkpointed per batch in `data/runtime/seeded.json`. |
| **Demo on a different day** | "Tomorrow" is still tomorrow. | Dates are stored relative to an anchor and shifted on first run. |

The failure paths are covered by tests that run with **no Hindsight and no API key** (`python -m pytest`).

## The data

All synthetic, and written to read like a real Hyderabad practice:

- **52 matters, 505 hearings, 246 adjournments** across 11 real forums: Nampally criminal courts, the Telangana High Court, City Civil Court, the MACT, the District Consumer Commission, the Family Court at Secunderabad, the ACB Special Court and the Labour Court.
- Real procedure and statutes: IPC 420/406/120-B, Section 138 NI Act, Section 65B certificates, Section 125 CrPC maintenance, GHMC demolition notices, M.V.O.P. claims.
- Realistic particulars: CNR numbers, crime numbers, cheque numbers, bank branches, survey numbers in Bachupally and Shamshabad, vehicle registrations (TS 09 EX 4417, Tata Ace Gold), seized devices (Samsung Galaxy S21 FE, SM-G990E), a Hikvision DS-7208HGHI-K1 DVR in an ACB trap case, and consumer goods by model number (Daikin FTKF50TV16U, Samsung WW80T504DAW).
- 13 judges and 12 opposite counsel, each with consistent **habits** (medical adjournments, time for instructions, last-minute compilations, maintainability objections), so patterns genuinely emerge *across* cases.
- One hand-written flagship case (*Reddy vs. State of Telangana*, 14 hearings) with planted threads: a pending certified bank statement, a defective 65B certificate, an amount that changes between the charge and the evidence, a judge transfer, and open client promises.

Regenerate it with `python scripts/generate_data.py`. It is deterministic.

## Run it

> [!NOTE]
> You need two keys: one for **Hindsight** (the memory) and one for **Groq** (the LLM that writes briefs). Both have free tiers.

### 1. Install

```bash
pip install -r requirements.txt
cp .env.example .env
```

### 2. Get a Hindsight instance

**Option A: Hindsight Cloud (recommended, nothing to install)**

1. Sign up at [ui.hindsight.vectorize.io](https://ui.hindsight.vectorize.io). In **Billing**, apply the promo code `MEMHACK99` for $50 of credit.
2. Click **Connect → Create API Key** and copy the key. It is only shown once.
3. In `.env`, set:
   ```env
   HINDSIGHT_URL=https://api.hindsight.vectorize.io
   HINDSIGHT_API_KEY=<your key>
   ```

**Option B: Local Docker**

```env
HINDSIGHT_URL=http://localhost:8888
HINDSIGHT_API_KEY=
HINDSIGHT_API_LLM_API_KEY=<your Groq key>   # Hindsight uses its own LLM for fact extraction
```
```bash
docker compose up -d        # API on :8888, Hindsight's own UI on :9999
```

### 3. Get a Groq key

Create one at [console.groq.com/keys](https://console.groq.com/keys) and set `LLM_API_KEY` in `.env`.

Groq's free tier allows about 8,000 tokens a minute per key, and one brief uses around 5,000. For a smooth live demo, add keys from one or two more accounts as `LLM_API_KEY_2` and `LLM_API_KEY_3`. The agent rotates across them automatically.

### 4. Check, seed, run

```bash
python scripts/check_setup.py      # verifies Hindsight + LLM, tells you exactly what is missing
python scripts/seed_memory.py      # retains the core set of hearings (~150) into Hindsight
python -m uvicorn app.main:app --port 8000
```

Open **http://localhost:8000**.

> [!TIP]
> Seeding sends each hearing through Hindsight's fact extraction, so it takes a few minutes. If it stops (rate limit, network), run the same command again and it resumes. `--scope all` loads all 505 hearings. `--fresh` wipes the bank and re-anchors dates to today.

## A three-minute demo

1. **The docket.** Eight matters tomorrow. Open *Reddy vs. State of Telangana*.
2. **The brief.** Point out the citations, the **3/4** adjournment pattern drawn from *other* cases, the line ready to say in court, and the amount that changed.
3. **Compare without memory.** A stateless assistant on the left, Case Diary on the right. This is the product.
4. **Memory up to hearing.** Drag to H3, then H8, then H14, and watch the brief get sharper.
5. **Log a hearing.** Use the sample note and save. *Understanding updated*: ₹38,50,000 → ₹40,00,000, and the statement moves from pending to produced. Regenerate the brief and it is already there.
6. **Bench & Bar.** Open Sri K. Venkateswara Rao or APP Chary for a profile built across every matter.
7. **Ctrl K.** Ask *"Which bail arguments have worked before Justice Varma?"* The answer comes from four different bail matters: parity and custody period worked, and long readings of judgments did not.

## Project layout

```
app/
  agent.py      brief, ask, log_hearing, profile: recall lanes, pattern detection, fallbacks
  memory.py     Hindsight wrapper: bank setup, retain, recall, reflect, circuit breaker
  llm.py        Groq client: retries, fallback model, tolerant JSON parsing
  diary.py      the advocate's record: cases, hearings, rendering to memory, offline recall
  prompts.py    system prompts (grounding and citation rules live here)
  main.py       FastAPI routes + static frontend
web/            index.html, styles.css, app.js (no build step)
scripts/
  generate_data.py   synthetic diary (deterministic)
  seed_memory.py     resumable load into Hindsight
  check_setup.py     connectivity check
data/diary.json      52 cases, 505 hearings
tests/               runs fully offline
```

## Guard rails

- Case Diary **never predicts outcomes** and never cites case law that is not in memory.
- Every factual line in a brief carries a hearing citation. Uncited claims are dropped.
- The advocate stays the decision-maker. The agent prepares and never advises.
- All names, cases and events in the dataset are fictional. Court names and procedure are real.

## Where this goes next

Import from the **eCourts** CNR status API so hearings arrive without typing, WhatsApp voice notes from the court corridor, a shared bank per chamber so juniors inherit the senior's memory of every bench, and Telugu and Hindi dictation.

---

<div align="center"><sub>Built for the <b>AI Agents That Learn Using Hindsight</b> hackathon.</sub></div>
