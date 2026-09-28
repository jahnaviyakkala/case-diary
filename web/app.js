/* Case Diary front end. No build step: plain DOM, hash routing. */

const $ = (s, el = document) => el.querySelector(s);
const main = $("#main");
const state = {
  memory: localStorage.getItem("cd.memory") !== "off",
  docket: null,
  briefs: new Map(),
  caseData: new Map(),
};

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const icons = () => window.lucide && lucide.createIcons();
const fmtDate = (iso, opts = { day: "numeric", month: "short", year: "numeric" }) =>
  iso ? new Date(iso + "T00:00:00").toLocaleDateString("en-IN", opts) : "";
const inr = (n) => (n ? "₹" + Number(n).toLocaleString("en-IN") : "");

function relDay(iso) {
  if (!iso || !state.docket) return "";
  const d = (new Date(iso + "T00:00:00") - new Date(state.docket.today + "T00:00:00")) / 864e5;
  if (d === 0) return "Today";
  if (d === 1) return "Tomorrow";
  if (d > 1 && d < 7) return fmtDate(iso, { weekday: "long" });
  return fmtDate(iso, { day: "numeric", month: "short" });
}

function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => (t.hidden = true), 3800);
}

async function api(path, opts = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch (_) {}
    throw new Error(typeof detail === "string" ? detail : "Request failed");
  }
  return res.json();
}

/* ---------------------------------------------------------------- shell */

function setMemory(on) {
  state.memory = on;
  localStorage.setItem("cd.memory", on ? "on" : "off");
  $("#memory-toggle").checked = on;
  $("#memory-state").textContent = on ? "on" : "off";
  document.body.classList.toggle("no-memory", !on);
}

function initTheme() {
  const saved = localStorage.getItem("cd.theme");
  if (saved) document.documentElement.dataset.theme = saved;
  $("#theme-toggle").onclick = () => {
    const dark = document.documentElement.dataset.theme === "dark" ||
      (!document.documentElement.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);
    const next = dark ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("cd.theme", next);
  };
}

async function refreshStatus() {
  try {
    const h = await api("/api/health");
    const set = (k, ok, title) => {
      const dot = $(`.dot[data-k="${k}"]`);
      dot.className = "dot " + (ok ? "ok" : "bad");
      dot.parentElement.title = title;
    };
    set("hindsight", h.hindsight.ok, h.hindsight.ok ? `Hindsight connected · bank ${h.hindsight.bank}` : `Hindsight offline: ${h.hindsight.error || ""}`);
    set("llm", h.llm.configured && !h.llm.last_error, h.llm.last_error ? `LLM: ${h.llm.last_error}` : `LLM ${h.llm.model}`);
    state.health = h;
  } catch (_) {}
}

function renderSidebar(activeId) {
  const d = state.docket;
  if (!d) return;
  $("#today").innerHTML = `
    <div class="dow">${fmtDate(d.today, { weekday: "long" })}</div>
    <div class="date">${fmtDate(d.today, { day: "numeric", month: "long", year: "numeric" })}</div>
    <div class="adv">${esc(d.advocate.name)} · ${d.totals.cases} matters</div>`;
  const groups = {};
  for (const c of d.upcoming) (groups[relDay(c.next_date)] ||= []).push(c);
  $("#docket").innerHTML = Object.entries(groups).map(([label, cs]) => `
    <div class="group-label"><span>${esc(label)}</span><span>${cs.length}</span></div>
    ${cs.map((c) => `
      <a class="docket-item ${c.id === activeId ? "active" : ""} ${c.id === "reddy-vs-state" ? "hero" : ""}" href="#/case/${c.id}/brief">
        <div class="t">${esc(c.title)}</div>
        <div class="s">${esc(c.next_purpose || c.type)}</div>
      </a>`).join("")}`).join("");
}

/* ---------------------------------------------------------------- routes */

async function route() {
  const parts = location.hash.replace(/^#\/?/, "").split("/");
  if (!state.docket) {
    try { state.docket = await api("/api/docket"); }
    catch (e) { main.innerHTML = `<div class="empty"><h2>The diary server is not responding</h2><p>${esc(e.message)}</p></div>`; return; }
  }
  const [page, id, tab] = parts;
  renderSidebar(page === "case" ? id : null);
  window.scrollTo(0, 0);
  if (page === "case" && id) return renderCase(id, tab || "brief");
  if (page === "people") return renderPeople(id);
  if (page === "all") return renderAll();
  return renderHome();
}

/* ---------------------------------------------------------------- home */

function renderHome() {
  const d = state.docket;
  const stats = state.health?.hindsight?.stats;
  const tomorrow = d.upcoming.filter((c) => relDay(c.next_date) === "Tomorrow").length;
  main.innerHTML = `
    <section class="home-hero">
      <h1>${tomorrow} matters tomorrow.<br><em>Your diary remembers all of them.</em></h1>
      <p>Every hearing you have logged, every direction from the bench, every adjournment and the reason given, and every promise to a client is kept in long-term memory. Ask for a brief and it is prepared from that record, with the source hearing cited.</p>
    </section>
    <div class="kpis">
      <div><b>${d.totals.cases}</b><span>active and recent matters</span></div>
      <div><b>${d.totals.hearings}</b><span>hearings in the diary</span></div>
      <div><b>${stats ? stats.world + stats.experience : "—"}</b><span>facts in Hindsight memory</span></div>
      <div><b>${stats ? stats.observation : "—"}</b><span>patterns learned across cases</span></div>
    </div>
    <div class="section"><h3><i data-lucide="calendar-days"></i> Cause list · next seven days</h3>
      ${d.upcoming.map((c) => `
        <a class="cause" href="#/case/${c.id}/brief">
          <div class="cd ${relDay(c.next_date) === "Tomorrow" ? "tm" : ""}">${esc(relDay(c.next_date))}</div>
          <div><div class="ct">${esc(c.title)}</div><div class="cs">${esc(c.case_no)} · ${esc(c.court_name)}</div></div>
          <div class="go">${esc(c.next_purpose || "")} <i data-lucide="arrow-right"></i></div>
        </a>`).join("")}
    </div>`;
  icons();
}

/* ---------------------------------------------------------------- case */

async function loadCase(id) {
  if (!state.caseData.has(id)) state.caseData.set(id, await api(`/api/cases/${id}`));
  return state.caseData.get(id);
}

async function renderCase(id, tab) {
  let data;
  try { data = await loadCase(id); }
  catch (e) { main.innerHTML = `<div class="empty"><h2>Case not found</h2><p>${esc(e.message)}</p></div>`; return; }
  const c = data.case;
  main.innerHTML = `
    <div class="court-line">${esc(c.court_name)}</div>
    <h1 class="case-title">${esc(c.title)}</h1>
    <div class="meta">
      <span class="mono">${esc(c.case_no)}</span>
      <span class="mono">CNR ${esc(c.cnr)}</span>
      <span><i data-lucide="gavel"></i>${esc(c.judge_name)}</span>
      <span><i data-lucide="user-round"></i>${esc(c.client.name)}, ${esc(c.client.role)}</span>
      <span><i data-lucide="swords"></i>${esc(c.opp_counsel_name)}</span>
      ${c.value ? `<span><i data-lucide="indian-rupee"></i>${inr(c.value)}</span>` : ""}
    </div>
    ${c.next_date ? `<div class="next"><span class="when">${esc(relDay(c.next_date))}</span>${esc(c.next_purpose || "")}</div>` : ""}
    <nav class="tabs">
      ${[["brief", "file-text", "Brief"], ["hearings", "history", "Hearings", data.hearings.length], ["log", "pen-line", "Log a hearing"]]
        .map(([k, ic, label, n]) => `<a class="tab ${tab === k ? "active" : ""}" href="#/case/${id}/${k}"><i data-lucide="${ic}"></i>${label}${n ? ` <span class="count">${n}</span>` : ""}</a>`).join("")}
    </nav>
    <div id="pane"></div>`;
  icons();
  if (tab === "hearings") return renderHearings(data);
  if (tab === "log") return renderLog(data);
  return renderBrief(data);
}

/* ---- brief ---- */

const LANES = { case: "This case", counsel: "Opposite counsel", judge: "Bench", ask: "Practice", learned: "Learned" };

function citeChip(fid, facts, caseId) {
  const f = facts.find((x) => x.fid === fid);
  if (!f) return "";
  const s = f.source;
  const label = s ? (s.case_id === caseId ? `H${s.no}` : `${s.case} · H${s.no}`) : fid;
  return `<button class="cite" data-fid="${fid}" title="${esc(f.text.slice(0, 180))}">${esc(label)}</button>`;
}
const cites = (arr, facts, caseId) => (arr || []).map((f) => citeChip(f, facts, caseId)).join("");

function loadingSteps(hearingCount) {
  const steps = state.memory
    ? [`Recalling ${hearingCount} hearings from Hindsight`, "Checking the bench and opposite counsel across other matters", "Reconciling facts that changed over time", "Drafting the brief"]
    : ["Reading the cause-list entry", "Drafting a brief without history"];
  return `<div class="loading"><ul class="steps">${steps.map((s, i) => `<li data-i="${i}"><span class="b"></span>${esc(s)}</li>`).join("")}</ul>
    <div class="sk" style="width:72%"></div><div class="sk" style="width:94%"></div><div class="sk" style="width:60%"></div></div>`;
}

function animateSteps(el) {
  const items = [...el.querySelectorAll(".steps li")];
  let i = 0;
  const tick = () => {
    items.forEach((li, k) => { li.className = k < i ? "done" : k === i ? "now" : ""; });
    if (i < items.length - 1) { i++; el._t = setTimeout(tick, 1100 + Math.random() * 700); }
  };
  tick();
  return () => clearTimeout(el._t);
}

async function fetchBrief(id, memory, asOf) {
  const key = `${id}|${memory}|${asOf || ""}`;
  if (!state.briefs.has(key)) {
    const p = api(`/api/cases/${id}/brief?memory=${memory}${asOf ? `&as_of=${asOf}` : ""}`);
    state.briefs.set(key, p);
    p.catch(() => state.briefs.delete(key));
  }
  return state.briefs.get(key);
}

async function renderBrief(data, opts = {}) {
  const pane = $("#pane");
  const id = data.case.id;
  const total = data.hearings.length;
  const asOf = opts.asOf && opts.asOf < total ? opts.asOf : null;
  const compare = !!opts.compare;
  pane.innerHTML = loadingSteps(total);
  const stop = animateSteps(pane);
  let b, generic;
  try {
    if (compare) [b, generic] = await Promise.all([fetchBrief(id, true, asOf), fetchBrief(id, false)]);
    else b = await fetchBrief(id, state.memory, state.memory ? asOf : null);
  } catch (e) {
    stop();
    pane.innerHTML = `<div class="banner off"><i data-lucide="triangle-alert"></i><div>Could not prepare the brief: ${esc(e.message)}. The hearing record is still available under Hearings.</div></div>`;
    icons();
    return;
  }
  stop();

  const toolbar = `
    <div class="toolbar">
      <button class="btn ${compare ? "on" : ""}" id="cmp"><i data-lucide="columns-2"></i>${compare ? "Comparing with a stateless assistant" : "Compare without memory"}</button>
      <button class="btn" id="regen"><i data-lucide="refresh-cw"></i>Regenerate</button>
      ${state.memory ? `<label class="depth" title="See how the brief improves as memory accumulates">
        <i data-lucide="layers"></i>Memory up to hearing
        <input type="range" id="depth" min="1" max="${total}" value="${asOf || total}">
        <b id="depth-val">${asOf ? `H${asOf}` : `all ${total}`}</b></label>` : ""}
    </div>`;

  const banners = [];
  if (b.mode === "memory" && b.memory_source === "offline")
    banners.push(`<div class="banner warn"><i data-lucide="cloud-off"></i><div><b>Hindsight is unreachable.</b> This brief was prepared from the local diary using keyword recall. Cross-case patterns may be incomplete.</div></div>`);
  if (b.composer === "template")
    banners.push(`<div class="banner warn"><i data-lucide="plug-zap"></i><div><b>Language model unavailable.</b> Showing recalled facts under each heading without synthesis. Nothing has been invented to fill the gaps.</div></div>`);
  if (b.mode === "stateless" && !compare)
    banners.push(`<div class="banner off"><i data-lucide="brain"></i><div><b>Memory is off.</b> This is what a stateless assistant can do with only tomorrow's cause-list entry.</div></div>`);

  if (compare) {
    pane.innerHTML = toolbar + banners.join("") + `
      <div class="brief-grid compare">
        <div class="stateless"><div class="col-label off"><i data-lucide="circle-slash"></i>Without memory</div>${briefBody(generic, id)}</div>
        <div><div class="col-label mem"><i data-lucide="brain"></i>With Hindsight memory · ${b.facts.length} facts recalled</div>${briefBody(b, id)}</div>
      </div>`;
  } else {
    pane.innerHTML = toolbar + banners.join("") + `
      <div class="brief-grid" style="${b.mode === "stateless" ? "grid-template-columns:1fr" : ""}">
        <div>${briefBody(b, id)}</div>
        ${b.mode === "memory" ? rail(b, id) : ""}
      </div>`;
  }
  icons();
  bindBrief(pane, data, b, { compare, asOf });
}

function patternCard(p, facts, caseId) {
  if (!p || (!p.total_matters && !p.in_this_case.length)) return "";
  const hitCites = p.matters.flatMap((m) => m.hearings).concat(p.in_this_case.map((h) => h.hearing_id));
  const fids = facts.filter((f) => f.source && hitCites.includes(f.source.hearing_id)).map((f) => f.fid);
  const ground = { medical: "medical grounds", witness: "absent witness / IO", documents: "documents not ready", instructions: "time for instructions" }[p.top_ground] || p.top_ground;
  return `
    <div class="pattern">
      <div class="big">${p.adjourned_matters}<small>/${p.total_matters}</small></div>
      <div class="what">of <b>${esc(p.counsel)}</b>'s last ${p.total_matters} other matters before ${esc(p.judge)} included an adjournment request${ground ? `, most often on ${esc(ground)}` : ""}.</div>
      <div class="dots">${p.matters.map((m) => `<span class="pd ${m.adjourned ? "hit" : ""}" title="${esc(m.title)}"><i></i>${esc(m.title.replace(/^State vs\. /, ""))}</span>`).join("")}</div>
      <div class="foot">In this case: ${p.in_this_case.length ? p.in_this_case.map((h) => `H${h.no} (${h.ground})`).join(", ") : "none so far"}. Counted only from hearings recalled from memory ${fids.slice(0, 6).map((f) => citeChip(f, facts, caseId)).join("")}</div>
    </div>`;
}

function briefBody(b, caseId) {
  const r = b.brief || {};
  const f = b.facts || [];
  const list = (items, key, icon, title, checkable) => (items && items.length ? `
    <div class="section"><h3><i data-lucide="${icon}"></i>${title}</h3><ul class="lined">
      ${items.map((it, i) => {
        const k = `cd.chk.${caseId}.${key}.${i}`;
        const done = checkable && localStorage.getItem(k) === "1";
        return `<li class="${done ? "done" : ""}">${checkable ? `<input type="checkbox" class="check" data-k="${k}" ${done ? "checked" : ""}>` : ""}<span class="txt">${esc(it.text)}${cites(it.cites, f, caseId)}</span></li>`;
      }).join("")}</ul></div>` : "");

  return `
    <h2 class="headline">${esc(r.headline)}</h2>
    <p class="standing">${esc(r.standing)}</p>
    ${b.mode === "memory" ? patternCard(b.pattern, f, caseId) : ""}
    ${r.last_time?.text ? `<div class="section"><h3><i data-lucide="rotate-ccw"></i>Last time</h3><p style="margin:0">${esc(r.last_time.text)}${cites(r.last_time.cites, f, caseId)}</p></div>` : ""}
    ${list(r.bench_expects, "bench", "gavel", "The bench expects")}
    ${(r.watch_outs || []).length ? `<div class="section"><h3><i data-lucide="eye"></i>Watch out</h3>
      ${r.watch_outs.map((w) => `<div class="watch"><div class="wt"><i data-lucide="triangle-alert"></i>${esc(w.title)}</div>${esc(w.text)}${cites(w.cites, f, caseId)}</div>`).join("")}</div>` : ""}
    ${r.preempt?.say ? `<div class="section"><h3><i data-lucide="message-square-quote"></i>Be ready to say</h3>
      <div class="script"><div class="trig">${esc(r.preempt.trigger)}</div><blockquote>“${esc(r.preempt.say)}”</blockquote>${cites(r.preempt.cites, f, caseId)}</div></div>` : ""}
    ${(r.changed || []).length ? `<div class="section"><h3><i data-lucide="git-compare"></i>Changed since it was first recorded</h3>
      ${r.changed.map((c) => `<div class="change"><div class="what">${esc(c.what)} ${cites(c.cites, f, caseId)}</div><div class="before">${esc(c.before)}</div><i data-lucide="arrow-right"></i><div class="after">${esc(c.after)}</div></div>`).join("")}</div>` : ""}
    ${list(r.promises, "promise", "handshake", "Promised to the client", true)}
    ${list(r.carry, "carry", "briefcase", "Carry to court", true)}
    ${(r.gaps || []).length ? `<div class="section"><h3><i data-lucide="circle-help"></i>Not in the record</h3><p class="gaps">${r.gaps.map(esc).join(" · ")}</p></div>` : ""}
    ${b.model ? `<p class="mono muted" style="margin-top:30px">${b.mode === "memory" ? `${f.length} memories · ` : ""}${esc(b.model)}</p>` : ""}`;
}

function rail(b, caseId) {
  const lanes = [...new Set(b.facts.map((x) => x.lane))];
  return `
    <aside class="rail">
      <div class="rail-head">
        <div class="rt"><i data-lucide="brain"></i>Recalled from memory</div>
        <div class="rs">${b.facts.length} facts · ${b.memory_source === "offline" ? "local diary (offline)" : "Hindsight bank"}</div>
        <div class="lanes"><button class="lane active" data-lane="">All</button>${lanes.map((l) => `<button class="lane" data-lane="${l}">${LANES[l] || l}</button>`).join("")}</div>
      </div>
      <div class="facts">${b.facts.map((x) => factRow(x, caseId)).join("")}</div>
    </aside>`;
}

function factRow(x, caseId) {
  const s = x.source;
  const isCorr = /^correction/i.test(x.text);
  const kind = isCorr ? "correction" : x.type === "observation" ? "observation" : x.type === "experience" ? "experience" : "fact";
  return `<div class="fact" data-fid="${x.fid}" data-lane="${x.lane}">
    <div class="fh"><span>${x.fid}</span>${s ? `<span class="src">${esc(s.case_id === caseId ? "This case" : s.case)} · H${s.no}</span><span>${fmtDate(s.date)}</span>` : x.date ? `<span>${fmtDate(x.date)}</span>` : ""}
    <span class="kind ${kind}">${kind === "observation" ? "learned" : kind}</span></div>${esc(x.text)}</div>`;
}

function bindBrief(pane, data, b, opts) {
  pane.querySelectorAll(".cite").forEach((el) => el.addEventListener("click", () => {
    const row = pane.querySelector(`.fact[data-fid="${el.dataset.fid}"]`);
    if (!row) return toast(el.title);
    pane.querySelectorAll(".lane").forEach((l) => l.classList.toggle("active", !l.dataset.lane));
    pane.querySelectorAll(".fact").forEach((r) => (r.style.display = ""));
    row.scrollIntoView({ behavior: "smooth", block: "center" });
    row.classList.add("flash");
    setTimeout(() => row.classList.remove("flash"), 1600);
  }));
  pane.querySelectorAll(".lane").forEach((btn) => btn.addEventListener("click", () => {
    pane.querySelectorAll(".lane").forEach((l) => l.classList.toggle("active", l === btn));
    pane.querySelectorAll(".fact").forEach((r) => (r.style.display = !btn.dataset.lane || r.dataset.lane === btn.dataset.lane ? "" : "none"));
  }));
  pane.querySelectorAll(".check").forEach((cb) => cb.addEventListener("change", () => {
    localStorage.setItem(cb.dataset.k, cb.checked ? "1" : "0");
    cb.closest("li").classList.toggle("done", cb.checked);
  }));
  $("#cmp").onclick = () => { if (!state.memory) setMemory(true); renderBrief(data, { ...opts, compare: !opts.compare }); };
  $("#regen").onclick = () => {
    [...state.briefs.keys()].filter((k) => k.startsWith(data.case.id + "|")).forEach((k) => state.briefs.delete(k));
    renderBrief(data, opts);
  };
  const depth = $("#depth");
  if (depth) {
    depth.oninput = () => ($("#depth-val").textContent = +depth.value === data.hearings.length ? `all ${data.hearings.length}` : `H${depth.value}`);
    depth.onchange = () => renderBrief(data, { ...opts, asOf: +depth.value });
  }
}

/* ---- hearings timeline ---- */

function renderHearings(data, filter = "all") {
  const pane = $("#pane");
  const hs = [...data.hearings].reverse().filter((h) =>
    filter === "all" ? true : filter === "adj" ? h.adjournment : filter === "asked" ? h.asked.length : h.promises.length);
  const adjLabel = (a) => ({ opposing: "Adjourned · opposite side", ours: "Adjourned · at our request", court: "Adjourned · court" }[a.by] || "Adjourned");
  pane.innerHTML = `
    <div class="filters">${[["all", "All"], ["adj", "Adjournments"], ["asked", "Bench directions"], ["promise", "Client promises"]]
      .map(([k, l]) => `<button class="lane ${k === filter ? "active" : ""}" data-f="${k}">${l}</button>`).join("")}</div>
    <div class="timeline">${hs.map((h) => `
      <div class="hearing ${h.adjournment ? "adj" : ""} ${h.logged ? "logged" : ""}">
        <div class="hh"><span class="no">H${h.no}</span><span class="hd">${fmtDate(h.date, { day: "numeric", month: "long", year: "numeric" })}</span><span class="stage">${esc(h.stage)} · ${esc(h.judge_name || "")}</span></div>
        <p>${esc(h.notes)}</p>
        <div class="chips">
          ${h.adjournment ? `<span class="chip adj"><i data-lucide="pause"></i>${adjLabel(h.adjournment)}: ${esc(h.adjournment.ground)}</span>` : ""}
          ${h.asked.map((a) => `<span class="chip ask"><i data-lucide="gavel"></i>${esc(a)}</span>`).join("")}
          ${h.due.map((x) => `<span class="chip"><i data-lucide="file-clock"></i>${esc(x.item)} · ${esc(x.by)} · ${esc(x.status)}</span>`).join("")}
          ${h.promises.map((p) => `<span class="chip promise"><i data-lucide="handshake"></i>${esc(p)}</span>`).join("")}
          ${h.lesson ? `<span class="chip"><i data-lucide="lightbulb"></i>${esc(h.lesson)}</span>` : ""}
        </div>
      </div>`).join("") || `<p class="muted">Nothing matches this filter.</p>`}</div>`;
  icons();
  pane.querySelectorAll("[data-f]").forEach((b) => (b.onclick = () => renderHearings(data, b.dataset.f)));
}

/* ---- log a hearing ---- */

const DEMO_NOTE = `PW-3 cross concluded today. Prosecution finally produced the full certified HDFC statement for Apr–Jun 2021, so that is no longer pending. On re-examination PW-3 said the total credited from the complainant was ₹40,00,000, not ₹38,50,000. APP Chary was present and did not seek time. Judge asked us to file our 5-page synopsis on the amount discrepancy before the next date. Next date 2026-10-27 for PW-4 (Investigating Officer). Promised Mr. Reddy the passport petition will be filed this week.`;

function renderLog(data) {
  const pane = $("#pane");
  pane.innerHTML = `
    <div class="log-grid">
      <div>
        <textarea id="note" placeholder="Dictate what happened in court today, the way you would tell your junior…"></textarea>
        <div class="row">
          <input type="date" id="hdate" value="${state.docket.today}">
          <button class="btn" id="demo"><i data-lucide="wand-sparkles"></i>Use sample note</button>
          <button class="btn primary" id="save"><i data-lucide="save"></i>Save to diary and memory</button>
        </div>
        <div id="log-result"></div>
      </div>
      <div class="aside-note">
        <h4>What happens when you save</h4>
        <ol>
          <li>The note is compared against everything memory holds for this case. Anything that <b>contradicts or updates</b> an earlier record is flagged.</li>
          <li>It is structured into adjournment, directions, documents due and client promises.</li>
          <li>It is retained in Hindsight with the hearing date. Corrections are stored as separate, newer memories, so the old fact is superseded rather than silently lost.</li>
          <li>If Hindsight is down, the note is kept in the local diary and queued. It syncs automatically when memory is back.</li>
        </ol>
      </div>
    </div>`;
  icons();
  $("#demo").onclick = () => ($("#note").value = data.case.id === "reddy-vs-state" ? DEMO_NOTE : "Matter called. Opposite counsel sought time citing illness. Judge granted a last chance and directed both sides to be ready. Next date 2026-11-12. Promised client a call this evening.");
  $("#save").onclick = async () => {
    const note = $("#note").value.trim();
    if (note.length < 10) return toast("Write a few lines about the hearing first.");
    const btn = $("#save");
    btn.disabled = true;
    btn.innerHTML = `<i data-lucide="loader"></i>Checking against memory…`;
    icons();
    try {
      const r = await api(`/api/cases/${data.case.id}/hearings`, { method: "POST", body: JSON.stringify({ note, date: $("#hdate").value }) });
      state.caseData.delete(data.case.id);
      [...state.briefs.keys()].filter((k) => k.startsWith(data.case.id + "|")).forEach((k) => state.briefs.delete(k));
      state.docket = await api("/api/docket");
      renderSidebar(data.case.id);
      $("#log-result").innerHTML = `
        <div class="result-card">
          <h4><i data-lucide="circle-check"></i>Saved as hearing ${r.hearing.no}</h4>
          <p style="margin:0 0 6px">${esc(r.hearing.notes)}</p>
          <p class="mono muted" style="margin:0">${r.retained} memor${r.retained === 1 ? "y" : "ies"} retained in Hindsight${r.queued ? ` · ${r.queued} queued (memory offline, will sync automatically)` : ""}</p>
          ${r.changes.length ? `<div class="updated"><h5><i data-lucide="git-compare"></i>Understanding updated</h5>
            ${r.changes.map((c) => `<div class="change"><div class="what">${esc(c.topic)}${c.before_source ? ` · was recorded at H${c.before_source.no}, ${fmtDate(c.before_source.date)}` : ""}</div><div class="before">${esc(c.before)}</div><i data-lucide="arrow-right"></i><div class="after">${esc(c.now)}</div></div>`).join("")}
          </div>` : `<p class="muted" style="margin:12px 0 0">Nothing in this note contradicts what memory already held.</p>`}
          <div class="row"><a class="btn" href="#/case/${data.case.id}/brief"><i data-lucide="file-text"></i>See the updated brief</a></div>
        </div>`;
      $("#note").value = "";
    } catch (e) {
      toast("Could not save: " + e.message);
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<i data-lucide="save"></i>Save to diary and memory`;
      icons();
    }
  };
}

/* ---------------------------------------------------------------- people */

async function renderPeople(active) {
  main.innerHTML = `<h1 class="page">Bench &amp; Bar</h1><p class="lede">What memory has learned about the judges you appear before and the counsel you appear against, gathered across every matter, not only one.</p><div class="sk" style="width:60%"></div>`;
  const p = await api("/api/people");
  const card = (x, kind) => `<button class="person ${active === `${kind}:${x.id}` ? "active" : ""}" data-kind="${kind}" data-id="${x.id}">
      <div class="pn">${esc(x.name)}</div><div class="pr">${esc(x.designation || x.role)}</div><div class="pc">${x.hearings} hearings in the diary</div></button>`;
  main.innerHTML = `
    <h1 class="page">Bench &amp; Bar</h1>
    <p class="lede">What memory has learned about the judges you appear before and the counsel you appear against, gathered across every matter, not only one.</p>
    <div id="profile"></div>
    <div class="section"><h3><i data-lucide="gavel"></i>Judges</h3><div class="people-grid">${p.judges.filter((j) => j.hearings).sort((a, b) => b.hearings - a.hearings).map((j) => card(j, "judge")).join("")}</div></div>
    <div class="section"><h3><i data-lucide="swords"></i>Opposite counsel</h3><div class="people-grid">${p.counsel.filter((c) => c.hearings).sort((a, b) => b.hearings - a.hearings).map((c) => card(c, "counsel")).join("")}</div></div>`;
  icons();
  main.querySelectorAll(".person").forEach((b) => (b.onclick = () => { location.hash = `#/people/${b.dataset.kind}:${b.dataset.id}`; }));
  if (active) showProfile(...active.split(":"));
}

async function showProfile(kind, id) {
  const el = $("#profile");
  el.innerHTML = `<div class="profile">${loadingSteps(0).replace(/Recalling 0 hearings from Hindsight/, "Recalling across all matters")}</div>`;
  const stop = animateSteps(el);
  try {
    const r = await api(`/api/people/${kind}/${id}`);
    stop();
    el.innerHTML = `<div class="profile">
      <div class="court-line">${esc(r.person.designation || r.person.role)}</div>
      <h2 class="headline" style="margin-top:6px">${esc(r.person.name)}</h2>
      <div class="stats"><div><b>${r.stats.cases}</b><span>matters</span></div><div><b>${r.stats.hearings}</b><span>hearings</span></div><div><b>${r.stats.adjournments_by_opposite}</b><span>adjournments sought by the other side</span></div></div>
      <p class="standing">${esc(r.profile.summary)}</p>
      <ul class="lined">${r.profile.points.map((pt) => `<li><span class="txt">${esc(pt.text)}${cites(pt.cites, r.facts, null)}</span></li>`).join("")}</ul>
      ${r.memory_source === "offline" ? `<div class="banner warn" style="margin-top:16px"><i data-lucide="cloud-off"></i><div>Hindsight offline: built from the local diary.</div></div>` : ""}
    </div>`;
    icons();
    el.querySelectorAll(".cite").forEach((c) => (c.onclick = () => toast(c.title)));
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (e) {
    stop();
    el.innerHTML = `<div class="banner off">Could not build the profile: ${esc(e.message)}</div>`;
  }
}

/* ---------------------------------------------------------------- all matters */

function renderAll() {
  const cs = state.docket.cases;
  main.innerHTML = `<h1 class="page">All matters</h1><p class="lede">${cs.length} matters across ${new Set(cs.map((c) => c.court)).size} courts.</p>
    <table class="matters"><thead><tr><th>Matter</th><th>Type</th><th>Court</th><th>Next date</th></tr></thead><tbody>
    ${cs.map((c) => `<tr data-id="${c.id}"><td><b style="font-weight:500">${esc(c.title)}</b><div class="mono muted">${esc(c.case_no)}</div></td><td>${esc(c.type)}</td><td class="muted">${esc(c.court_name)}</td><td class="mono">${c.next_date ? fmtDate(c.next_date) : "Disposed"}</td></tr>`).join("")}
    </tbody></table>`;
  main.querySelectorAll("tr[data-id]").forEach((tr) => (tr.onclick = () => (location.hash = `#/case/${tr.dataset.id}/brief`)));
}

/* ---------------------------------------------------------------- palette */

function openPalette() {
  $("#palette").hidden = false;
  $("#palette-answer").innerHTML = "";
  $("#palette-input").value = "";
  $("#palette-input").focus();
}
function closePalette() { $("#palette").hidden = true; }

async function runQuery(q) {
  q = q.trim();
  if (!q) return;
  const ans = $("#palette-answer");
  if (/^(prep|prepare|brief)\b/i.test(q)) {
    const r = await api(`/api/resolve?q=${encodeURIComponent(q)}`);
    if (r.case) { closePalette(); location.hash = `#/case/${r.case}/brief`; return; }
    ans.innerHTML = r.suggestions.length
      ? `<p class="muted">Which matter did you mean?</p>${r.suggestions.map((s) => `<a class="cause" style="grid-template-columns:1fr" href="#/case/${s.id}/brief"><div class="ct">${esc(s.title)}</div></a>`).join("")}`
      : `<p class="muted">I could not find a matter matching that. Try the party name or case number.</p>`;
    ans.querySelectorAll("a").forEach((a) => (a.onclick = closePalette));
    return;
  }
  ans.innerHTML = `<div class="sk" style="width:80%"></div><div class="sk" style="width:65%"></div>`;
  try {
    const r = await api("/api/ask", { method: "POST", body: JSON.stringify({ question: q }) });
    const text = esc(r.answer).replace(/\[(F\d+)\]/g, (_, fid) => citeChip(fid, r.facts, r.case_id) || "");
    ans.innerHTML = `<div class="answer">${text}</div>
      ${r.memory_source === "offline" ? `<div class="banner warn" style="margin-top:12px">Hindsight offline: answered from the local diary.</div>` : ""}
      <p class="mono muted" style="margin:14px 0 0">${r.facts.length} memories consulted</p>`;
    ans.querySelectorAll(".cite").forEach((c) => (c.onclick = () => toast(c.title)));
  } catch (e) {
    ans.innerHTML = `<div class="banner off">${esc(e.message)}</div>`;
  }
}

/* ---------------------------------------------------------------- boot */

setMemory(state.memory);
initTheme();
$("#memory-toggle").addEventListener("change", (e) => {
  setMemory(e.target.checked);
  if (location.hash.includes("/brief")) route();
});
$("#command-open").onclick = openPalette;
$("#palette").addEventListener("click", (e) => { if (e.target.id === "palette") closePalette(); });
$("#palette-form").addEventListener("submit", (e) => { e.preventDefault(); runQuery($("#palette-input").value); });
document.querySelectorAll(".palette-hints button").forEach((b) => (b.onclick = () => { $("#palette-input").value = b.dataset.q; runQuery(b.dataset.q); }));
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openPalette(); }
  if (e.key === "Escape") closePalette();
});
window.addEventListener("hashchange", route);
refreshStatus().then(() => { if (!location.hash || location.hash === "#/") renderHome(); });
setInterval(refreshStatus, 30000);
route();
icons();
