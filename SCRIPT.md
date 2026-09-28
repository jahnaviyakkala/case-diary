<div align="center">

# Case Diary · Team Guide & Demo Script

**Setup · Project map · Technical summary · Live walkthrough**

</div>

---

> [!IMPORTANT]
> Read **Part 1** once and set up at least a day before the demo. On the demo day itself, only **Part 4** matters.

---

## Contents

| Part | What it covers | Time needed |
|:---:|---|:---:|
| **1** | Setting up on your machine | 10 min |
| **2** | What is where in the repo | 3 min read |
| **3** | Technical summary, for judges' questions | 5 min read |
| **4** | The demo script: what to click, what to say, when to pause | ~5 min on stage |
| **5** | If something goes wrong on stage | reference |

---

## Part 1 · Setup

### ① Get the code

```bash
git clone https://github.com/jahnaviyakkala/case-diary.git
cd case-diary
```

### ② Put the `.env` file in place

You'll receive the contents of a `.env` file privately.

1. Create a file named exactly **`.env`** in the **root** of the project, the same folder as `README.md`.
2. Paste the contents in and save.

```
case-diary/
├── .env          ← here
├── README.md
├── app/
└── ...
```

> [!CAUTION]
> Never commit `.env` or paste it anywhere public. It holds the Hindsight and Groq keys. It's already listed in `.gitignore`.

### ③ Install dependencies

Python 3.10 or newer.

```bash
pip install -r requirements.txt
```

### ④ Check that everything connects

```bash
python scripts/check_setup.py
```

You should see:

```
  [ ok ] Hindsight is reachable
  [ ok ] bank 'case-diary': 387 facts, 38 experiences, 132 learned observations
  [ ok ] recall works
  [ ok ] key 1 answers on openai/gpt-oss-120b
  [ ok ] key 2 answers on openai/gpt-oss-120b
  [ ok ] key 3 answers on openai/gpt-oss-120b
All good.
```

**The memory bank is already seeded and shared.** Everyone using this `.env` sees the same memory, so there's nothing to load.

### ⑤ On the demo day: reset the dates (one person only)

The demo tells the story that Reddy's hearing is **tomorrow**. Dates are fixed to the day memory was seeded, so on the demo morning **one person** runs:

```bash
python scripts/seed_memory.py --fresh
```

This takes about **7 minutes**. It wipes the shared bank, moves every date so "tomorrow" is really tomorrow, and reloads all 146 hearings. If it stops halfway, run the same command **without** `--fresh` and it resumes.

> [!WARNING]
> Only **one** teammate should run `--fresh`, because the bank is shared. Everyone else then deletes their local `data/runtime/` folder so their dates match.

### ⑥ Run the app

```bash
python -m uvicorn app.main:app --port 8000
```

Open **http://localhost:8000**. Chrome or Edge, full screen, zoom at 100%.

---

## Part 2 · What is where

```
case-diary/
│
├── app/                  ◆ the backend (Python, FastAPI)
│   ├── agent.py            the brain: brief, Q&A, log hearing, profiles, fallbacks
│   ├── memory.py           everything that talks to Hindsight (retain, recall)
│   ├── llm.py              Groq client: 3-key rotation, fallback model, JSON repair
│   ├── diary.py            the advocate's own record; renders hearings into memory
│   ├── prompts.py          the rules the model must follow (cite or omit)
│   └── main.py             API routes and the web page server
│
├── web/                  ◆ the frontend (plain HTML/CSS/JS, no build step)
│   ├── index.html
│   ├── styles.css          the "chambers" theme, light and dark
│   └── app.js              docket, brief, timeline, log, Bench & Bar, Ctrl+K
│
├── scripts/              ◆ one-off tools
│   ├── generate_data.py    builds the synthetic diary (52 matters, 505 hearings)
│   ├── seed_memory.py      loads hearings into Hindsight (resumable, --fresh)
│   ├── check_setup.py      tests Hindsight and every key
│   └── make_charts.py      draws the README charts
│
├── data/diary.json       ◆ the dataset
├── docs/                 ◆ screenshots and charts used in the README
├── tests/                ◆ 8 tests that run with no internet or keys
├── README.md             ◆ the public project page
└── SCRIPT.md             ◆ this file
```

---

## Part 3 · Technical summary

> **In one line:** an agent that prepares a litigation lawyer for tomorrow's hearing using long-term memory of every past hearing, across every case, and shows its sources.

### The flow of one brief

```
 "Prep me for Reddy"
        │
        ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  6 parallel Hindsight recalls, each scoped by tags           │
 │  case:reddy  ×3   ·   counsel:Chary   ·   judge:Rao  ×2      │
 └──────────────────────────────────────────────────────────────┘
        │  ~100 facts, each tied to a hearing id
        ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  Pattern maths on the recalled hearings only                 │
 │  → "Chary adjourned in 3 of his last 4 matters here"         │
 └──────────────────────────────────────────────────────────────┘
        │
        ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  gpt-oss-120b writes the brief from numbered facts [F1..Fn]  │
 │  Every line must cite facts. Invented citations are dropped. │
 └──────────────────────────────────────────────────────────────┘
        │
        ▼
   Brief + memory rail + pattern card
```

### Key points to know

| Topic | What to say |
|---|---|
| **Stack** | Python and FastAPI backend, vanilla JS frontend, **Hindsight Cloud** for memory, **Groq** (`gpt-oss-120b`) for writing. |
| **What goes into memory** | Each hearing is retained as a dated memory with tags `case:`, `judge:`, `counsel:`, `court:` and metadata (hearing number, who adjourned, on what ground). The hearing id is the `document_id`, so re-seeding never duplicates. |
| **Bank configuration** | A `retain_mission` tells Hindsight what matters in a court note. An `observations_mission` makes it learn behaviour of judges and counsel **across cases**. A **directive** forbids stating anything not in memory. |
| **Learned observations** | Hindsight forms patterns on its own (132 right now). They show as **LEARNED** in the memory rail. |
| **Contradictions** | A new note is checked against memory. Changes are shown as before → after, and each is **retained as its own dated correction**, so the old fact is superseded rather than erased. |
| **Learning curve** | The "Memory up to hearing" slider filters recall to hearings ≤ N. H3 gives a thin brief; H14 a sharp one. |
| **Grounding** | The model gets numbered facts. Citations are validated against the recalled set, and anything uncited is dropped. |
| **Failure handling** | Hindsight down → answers from the local diary with a banner. Groq rate-limited → rotate across 3 keys, then a fallback model. No model at all → recalled facts shown without synthesis. Saves while memory is down are queued and replayed. |
| **Data** | 52 matters, 505 hearings across 11 real Hyderabad courts. Real statutes, CNR numbers, rupee amounts, device model numbers. All people and events fictional. |
| **Tests** | `python -m pytest`, which runs fully offline and covers the fallback paths. |

---

## Part 4 · The demo script

> [!TIP]
> **How to read this:**
> 🖱️ **DO** is what to click or type.
> 🎤 **SAY** is what to say, word for word or in your own words.
> ⏸️ **PAUSE** is where the screen is loading. Keep talking and use the filler line given.

<br>

### ⏱ Before you go on stage (5 min earlier)

- [ ] App running, browser open at `http://localhost:8000`, full screen
- [ ] **Open the Reddy brief once** so it's cached and loads instantly on stage
- [ ] Toggle **Memory on** (top right, green)
- [ ] Light theme (moon icon, top right, toggles it)
- [ ] Close other tabs and silence notifications

---

### 🎬 Scene 1 · The problem &nbsp;·&nbsp; *0:00 – 0:40*

🖱️ **DO:** Stay on the home page (the docket).

🎤 **SAY:**
> "India has over five crore pending cases. A single criminal trial runs four or five years, fifteen hearings, most of them adjourned. A lawyer carries a hundred or more such matters, and the only memory is a paper diary.
>
> The night before a hearing, what they need isn't legal research. It's **recall**: what happened last time, what the judge asked for, what they promised the client, and how this judge and this opposing counsel behave.
>
> This is Case Diary. Tomorrow's cause list is on screen: eight matters, fifty-two in the diary, and underneath it a **Hindsight memory bank** with every hearing."

🖱️ **DO:** Point at the green numbers: *facts held in Hindsight* and *patterns learned across cases*.

---

### 🎬 Scene 2 · The brief &nbsp;·&nbsp; *0:40 – 2:00*

🖱️ **DO:** Press **Ctrl + K**, type **"Prep me for tomorrow's hearing in Reddy vs. State"**, press Enter.

⏸️ **PAUSE** (instant if pre-cached; otherwise 10–15 s while the steps tick)
> 🎤 *Filler:* "It's recalling fourteen hearings across three and a half years, and at the same time checking this judge and this prosecutor across **other** cases."

🎤 **SAY** (once the brief appears):
> "Every line here cites the hearing it came from. These small green tabs, H14, H12, are sources."

🖱️ **DO:** Click one citation tab, e.g. **H14**. The fact highlights in the right-hand rail.

🎤 **SAY:**
> "That's the actual memory Hindsight returned. Nothing on this page is invented."

🖱️ **DO:** Point at the **3/4 card**.

🎤 **SAY:**
> "This is the part a paper diary can't do. The prosecutor, APP Chary, asked for an adjournment in **three of his last four matters** before this judge, mostly on medical grounds. Those are **other** files. Memory connected them."

🖱️ **DO:** Scroll down slowly to **Be ready to say**, then **Changed since it was first recorded**.

🎤 **SAY:**
> "It gives the lawyer a line to say in court. And it caught that the amount changed: ₹42 lakh in the charge, ₹38.5 lakh in the witness's own evidence at hearing seven. That's a cross-examination point."

🖱️ **DO:** Scroll to **Promised to the client**.

🎤 **SAY:**
> "And the promise made to the client about his passport, for his daughter's wedding, is still open."

---

### 🎬 Scene 3 · Memory off vs on &nbsp;·&nbsp; *2:00 – 2:40*

🖱️ **DO:** Scroll up and click **Compare without memory**.

⏸️ **PAUSE** (2–5 s)
> 🎤 *Filler:* "Same request, same model, one without memory."

🎤 **SAY:**
> "On the left is a stateless assistant: generic advice about cross-examination, true of any case. On the right is Case Diary: this bench, this prosecutor, this client. **The only difference is memory.**"

🖱️ **DO:** Click **Compare without memory** again to close it.

---

### 🎬 Scene 4 · It gets smarter over time &nbsp;·&nbsp; *2:40 – 3:20*

🖱️ **DO:** Drag the **Memory up to hearing** slider (top right of the brief) to **H3** and release.

⏸️ **PAUSE** (5–10 s)
> 🎤 *Filler:* "This rewinds memory to what the diary knew after hearing three."

🎤 **SAY:**
> "After three hearings the brief is thin. There's no pattern yet and no discrepancy."

🖱️ **DO:** Drag the slider back to the far right (**all 14**).

🎤 **SAY:**
> "After fourteen, it knows the bench's habits, the prosecutor's pattern and the open promises. **Every hearing makes it sharper.**"

---

### 🎬 Scene 5 · Facts change &nbsp;·&nbsp; *3:20 – 4:20*

🖱️ **DO:** Click the **Log a hearing** tab. Click **Use sample note**.

🎤 **SAY** (while the note is visible):
> "Say today's hearing just happened. The lawyer dictates a quick note: the bank statement finally came, and the witness now says forty lakh, not thirty-eight and a half."

🖱️ **DO:** Click **Save to diary and memory**.

⏸️ **PAUSE** (10–20 s, the longest wait)
> 🎤 *Filler:* "It's comparing this note against everything memory holds about the case, looking for anything that contradicts an earlier record. Then it saves the hearing into Hindsight, and saves each correction as its own dated memory, so the old fact is superseded, not silently deleted. That's how a lawyer treats a record."

🎤 **SAY** (when **Understanding updated** appears):
> "It caught the amount change and tells us exactly where the old figure came from: hearing seven. It also caught that the bank statement is no longer pending, and that the cross-examination has concluded."

> [!NOTE]
> After this step, Reddy moves off "Tomorrow" because the new hearing set a new date. That's correct behaviour. Don't go back to the docket after this.

---

### 🎬 Scene 6 · Knowledge across cases &nbsp;·&nbsp; *4:20 – 5:00*

🖱️ **DO:** Press **Ctrl + K** and click **"Which bail arguments have worked before Justice Varma?"**

⏸️ **PAUSE** (2–5 s)
> 🎤 *Filler:* "This question isn't about any one case."

🎤 **SAY:**
> "The answer comes from **three separate bail matters**: parity with co-accused and time in custody worked, and long readings of judgments didn't. That's the kind of thing senior lawyers carry in their heads for twenty years."

🖱️ **DO:** Press **Esc**. *(Optional, if time allows:)* click **Bench & Bar** in the sidebar, then **Sri B. Narasimha Chary**.

---

### 🎬 Close &nbsp;·&nbsp; *5:00*

🎤 **SAY:**
> "Case Diary runs on Hindsight: every hearing retained with its date and tags, recalled by case, by judge and by counsel, and consolidated into patterns it learns on its own. If memory or the model goes down, it still works and tells you so. Five crore pending cases, and every lawyer behind them deserves a diary that remembers. Thank you."

---

## Part 5 · If something goes wrong on stage

| You see | Do this | Say this |
|---|---|---|
| Amber banner **"Hindsight is unreachable"** | Carry on. The brief still works from the local diary. | *"And that's the fallback: memory is down, so it answers from the local diary and tells you so."* |
| Amber banner **"Language model unavailable"** | Carry on. Facts are still listed. | *"The model's offline, so it shows the recalled facts as they are and doesn't make anything up."* |
| Brief takes over 20 s | Wait. Keys rotate automatically. | Use the Scene 2 filler line. |
| Page blank or broken | Refresh the browser (F5). | *"Let me refresh that."* |
| Server window closed | Re-run `python -m uvicorn app.main:app --port 8000` | — |
| Reddy isn't under "Tomorrow" | Someone logged a hearing earlier. Open it via Ctrl + K → *Prep me for Reddy*. | — |

---

<div align="center">

**Checklist:** `.env` in root ✔ &nbsp;·&nbsp; `check_setup` all ok ✔ &nbsp;·&nbsp; `--fresh` run on demo morning ✔ &nbsp;·&nbsp; Reddy brief pre-opened ✔

</div>
