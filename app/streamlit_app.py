# app/streamlit_app.py
# ✅ COMPLETE Streamlit app (single file)
# ✅ Keeps ALL features you already have
# ✅ Makes Dashboard professional + clean (less messy)
# ✅ Chat window stays like a real chat app

import os
import time
import requests
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# -----------------------------
# Config
# -----------------------------
API_URL = os.getenv("MOODYBOT_API_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(
    page_title="MoodyBot 3.0",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# API helpers
# -----------------------------
def api_get(path, params=None):
    r = requests.get(f"{API_URL}{path}", params=params, timeout=60)
    r.raise_for_status()
    return r.json()

def api_post(path, payload):
    r = requests.post(f"{API_URL}{path}", json=payload, timeout=220)
    r.raise_for_status()
    return r.json()

def api_patch(path, payload):
    r = requests.patch(f"{API_URL}{path}", json=payload, timeout=220)
    r.raise_for_status()
    return r.json()

def api_delete(path):
    r = requests.delete(f"{API_URL}{path}", timeout=160)
    r.raise_for_status()
    return r.json()

# -----------------------------
# State init
# -----------------------------
def init_state():
    if "chat_work" not in st.session_state:
        st.session_state.chat_work = []
    if "chat_personal" not in st.session_state:
        st.session_state.chat_personal = []
    if "last_stats" not in st.session_state:
        st.session_state.last_stats = {"level": 1, "current_streak": 0, "xp": 0}
    if "active_mode" not in st.session_state:
        st.session_state.active_mode = "work"
    if "last_reprio" not in st.session_state:
        st.session_state.last_reprio = []
    if "task_event_map" not in st.session_state:
        st.session_state.task_event_map = {}
    if "next_best_action" not in st.session_state:
        st.session_state.next_best_action = False

    # dashboard controls (kept, just cleaner defaults)
    if "dash_task_limit" not in st.session_state:
        st.session_state.dash_task_limit = 7
    if "dash_show_completed" not in st.session_state:
        st.session_state.dash_show_completed = False

init_state()

# -----------------------------
# Styling (PRO + clean + dark safe)
# -----------------------------
st.markdown(
    """
<style>
:root{
  --mb-text: var(--text-color, rgba(255,255,255,0.92));
  --mb-muted: rgba(148,163,184,0.95);
  --mb-line: rgba(148,163,184,0.22);

  --mb-accent: rgba(59,130,246,0.95);
  --mb-accent-soft: rgba(59,130,246,0.14);
}
section.main > div { padding-top: 0.5rem; }

/* Top header */
.mb-top{
  border-radius:18px;
  padding:14px 16px;
  background: linear-gradient(135deg, var(--mb-accent-soft), rgba(255,255,255,0.02));
  border:1px solid rgba(59,130,246,0.22);
  margin-bottom:12px;
}
.mb-top-grid{ display:flex; gap:10px; align-items:stretch; flex-wrap:wrap; }
.mb-brand, .mb-metric{
  background: rgba(255,255,255,0.03);
  border:1px solid var(--mb-line);
  border-radius:16px;
  padding:12px 14px;
  backdrop-filter: blur(8px);
}
.mb-brand{ flex: 2; min-width: 260px; }
.mb-brand h1{ font-size:18px; margin:0; color: var(--mb-text); }
.mb-brand .sub{ margin-top:2px; font-size:12px; color: var(--mb-muted); }
.mb-metric{ flex: 1; min-width: 150px; }
.mb-metric .k{ font-size:12px; color: var(--mb-muted); margin-bottom:2px; }
.mb-metric .v{ font-size:18px; color: var(--mb-text); font-weight:700; }
.mb-metric .hint{ font-size:12px; color: var(--mb-muted); margin-top:2px; }

/* Cards */
.card{
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--mb-line);
  border-radius: 18px;
  padding: 14px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.20);
}
.card-title{ font-weight:800; color:var(--mb-text); font-size: 15px; margin:0 0 3px 0; }
.card-sub{ color: var(--mb-muted); font-size: 12px; margin:0 0 8px 0; }
.hr{ height:1px; background:var(--mb-line); margin:10px 0; }

/* Pills + badges */
.pill{
  display:inline-block;
  font-size:12px;
  padding:2px 10px;
  border-radius:999px;
  background: rgba(59,130,246,0.14);
  border:1px solid rgba(59,130,246,0.25);
  color: rgba(219,234,254,0.95);
}
.pill-gray{
  background: rgba(148,163,184,0.12);
  border:1px solid rgba(148,163,184,0.22);
  color: rgba(226,232,240,0.92);
}
.badge{
  display:inline-block; padding:2px 10px; border-radius:999px;
  font-size:12px; border:1px solid rgba(148,163,184,0.22);
  background: rgba(148,163,184,0.12);
  color: rgba(226,232,240,0.92);
}
.badge-high{ background: rgba(239,68,68,0.16); border-color: rgba(239,68,68,0.28); color: rgba(254,226,226,0.95); }
.badge-med{ background: rgba(245,158,11,0.16); border-color: rgba(245,158,11,0.28); color: rgba(255,237,213,0.95); }
.badge-low{ background: rgba(34,197,94,0.14); border-color: rgba(34,197,94,0.26); color: rgba(220,252,231,0.95); }

/* Task row (compact + clean) */
.trow{
  display:flex; align-items:flex-start; gap:10px;
  padding:10px 10px;
  border:1px solid rgba(148,163,184,0.22);
  background: rgba(255,255,255,0.03);
  border-radius:14px;
  margin:8px 0;
}
.tleft{ flex:1; min-width: 0; }
.ttitle{
  font-size:14px; color:var(--mb-text); font-weight:650; line-height:1.2;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
}
.tmeta{ font-size:12px; color:var(--mb-muted); margin-top:2px; display:flex; gap:8px; flex-wrap:wrap; }
.done .ttitle{ text-decoration: line-through; color: rgba(148,163,184,0.95); }

div.stButton>button { border-radius: 12px; padding: 0.45rem 0.8rem; }
div[data-testid="stTextArea"] textarea{ border-radius: 14px !important; }
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# Helpers
# -----------------------------
def priority_badge(p):
    p = (p or "medium").lower()
    if p == "high":
        return "<span class='badge badge-high'>High</span>"
    if p == "medium":
        return "<span class='badge badge-med'>Medium</span>"
    return "<span class='badge badge-low'>Low</span>"

def parse_iso_safe(s):
    if not s or s == "unscheduled":
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None

def is_scheduled(t):
    stime = t.get("scheduled_time")
    return stime and stime != "unscheduled" and parse_iso_safe(stime) is not None

def task_status(t):
    return (t.get("status") or "planned").lower()

def compute_reprio_deltas(before_tasks, after_tasks):
    b = {t["id"]: t for t in before_tasks}
    a = {t["id"]: t for t in after_tasks}
    deltas = []
    for tid, at in a.items():
        bt = b.get(tid)
        if not bt:
            continue
        changed = False
        delta = {"id": tid, "description": at.get("description", ""), "changes": []}

        if bt.get("effective_priority") != at.get("effective_priority"):
            changed = True
            delta["changes"].append(
                f"Priority: {bt.get('effective_priority')} → {at.get('effective_priority')}"
            )

        if (bt.get("scheduled_time") or "") != (at.get("scheduled_time") or ""):
            changed = True
            delta["changes"].append(
                f"Scheduled: {bt.get('scheduled_time')} → {at.get('scheduled_time')}"
            )

        if changed:
            deltas.append(delta)
    return deltas[:12]

def group_tasks(tasks):
    now = datetime.now()
    week_end = now + timedelta(days=7)

    today, week, later = [], [], []
    for t in tasks:
        if task_status(t) == "skipped":
            continue
        if not st.session_state.dash_show_completed and task_status(t) == "done":
            continue

        dt = parse_iso_safe(t.get("scheduled_time"))
        if dt is None:
            later.append(t)
            continue
        if dt.date() == now.date():
            today.append(t)
        elif now <= dt <= week_end:
            week.append(t)
        else:
            later.append(t)

    today.sort(key=lambda x: parse_iso_safe(x.get("scheduled_time")) or datetime.max)
    week.sort(key=lambda x: parse_iso_safe(x.get("scheduled_time")) or datetime.max)

    pr = {"high": 0, "medium": 1, "low": 2}
    later.sort(key=lambda x: (pr.get((x.get("effective_priority") or "medium").lower(), 1), -x.get("id", 0)))
    return today, week, later

def pick_next_best_action(tasks):
    planned = [t for t in tasks if task_status(t) not in {"done", "skipped"}]
    if not planned:
        return None

    pr = {"high": 0, "medium": 1, "low": 2}
    def key(t):
        dt = parse_iso_safe(t.get("scheduled_time"))
        dt_key = dt if dt else datetime.max
        ep = (t.get("effective_priority") or t.get("user_priority") or "medium").lower()
        return (dt_key, pr.get(ep, 1), -t.get("id", 0))

    planned.sort(key=key)
    return planned[0]

def animate_xp_gain(xp_before, xp_after):
    if xp_after <= xp_before:
        return
    delta = xp_after - xp_before
    box = st.empty()
    steps = min(14, max(6, delta))
    for i in range(steps + 1):
        v = xp_before + int(delta * (i / steps))
        box.metric("XP", v, f"+{v - xp_before}")
        time.sleep(0.03)
    box.empty()

def mirror_task_to_schedule(task):
    try:
        tid = task.get("id")
        stime = task.get("scheduled_time")
        desc = (task.get("description") or "").strip()
        if not tid or not desc or not is_scheduled(task):
            return
        if tid in st.session_state.task_event_map:
            return
        title = f"Task: {desc}"
        api_post("/schedule", {"title": title, "start_time": stime})
        st.session_state.task_event_map[tid] = title
    except Exception:
        return

def send_chat_and_update(text: str, mode="work", auto_add=True, auto_schedule=True, default_priority="medium"):
    try:
        before = api_get("/tasks", params={"mode": mode}).get("tasks", [])
    except Exception:
        before = api_get("/tasks").get("tasks", [])

    try:
        stats_before = api_get("/gamification")
    except Exception:
        stats_before = st.session_state.last_stats

    out = api_post("/ai/chat", {
        "text": text,
        "default_mode": mode,
        "default_priority": default_priority,
        "auto_add": auto_add,
        "auto_schedule": auto_schedule,
    })

    try:
        after = api_get("/tasks", params={"mode": mode}).get("tasks", [])
    except Exception:
        after = api_get("/tasks").get("tasks", [])

    st.session_state.last_reprio = compute_reprio_deltas(before, after)

    try:
        stats_after = api_get("/gamification")
    except Exception:
        stats_after = stats_before

    if stats_after.get("current_streak", 0) > stats_before.get("current_streak", 0):
        st.balloons()

    if stats_after.get("xp", 0) > stats_before.get("xp", 0):
        animate_xp_gain(stats_before.get("xp", 0), stats_after.get("xp", 0))

    st.session_state.last_stats = stats_after

    if out.get("type") == "task_created":
        mirror_task_to_schedule(out.get("task", {}))
    if out.get("type") == "assistant_reply":
        for t in out.get("auto_added", []) or []:
            mirror_task_to_schedule(t)
        for t in out.get("created_tasks", []) or []:
            mirror_task_to_schedule(t)

    return out

def header_bar(stats):
    today = datetime.now().strftime("%A, %d %B")
    mode_label = "Workspace" if st.session_state.active_mode == "work" else "Personal"

    st.markdown(
        f"""
<div class="mb-top">
  <div class="mb-top-grid">
    <div class="mb-brand">
      <h1>MoodyBot 3.0</h1>
      <div class="sub">{today} • Mode: <span class="pill">{mode_label}</span></div>
    </div>
    <div class="mb-metric">
      <div class="k">Level</div>
      <div class="v">{stats.get("level",1)}</div>
      <div class="hint">Keep it consistent</div>
    </div>
    <div class="mb-metric">
      <div class="k">Streak</div>
      <div class="v">{stats.get("current_streak",0)} days</div>
      <div class="hint">Confetti on increase</div>
    </div>
    <div class="mb-metric">
      <div class="k">XP</div>
      <div class="v">{stats.get("xp",0)}</div>
      <div class="hint">Animated on gain</div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

def task_row(t, allow_done_button=False, done_key_prefix="done"):
    desc = (t.get("description") or "").strip()
    stime = t.get("scheduled_time", "unscheduled")
    ep = (t.get("effective_priority") or t.get("user_priority") or "medium").lower()
    status = task_status(t)

    when = "Later"
    if is_scheduled(t):
        dt = parse_iso_safe(stime)
        when = dt.strftime("%d %b • %H:%M") if dt else stime

    done_class = "done" if status == "done" else ""
    st.markdown(
        f"""
<div class="trow {done_class}">
  <div class="tleft">
    <div class="ttitle">{desc}</div>
    <div class="tmeta">
      <span class="pill-gray">{t.get("mode","")}</span>
      <span class="pill">⏰ {when}</span>
      {priority_badge(ep)}
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    if allow_done_button and status != "done":
        if st.button("✅ Complete", key=f"{done_key_prefix}_{t['id']}"):
            api_post("/feedback", {
                "task_id": t["id"],
                "mood": "neutral",
                "mode": t.get("mode", st.session_state.active_mode),
                "task_type": "general",
                "completed": True,
                "user_priority": t.get("user_priority", "medium"),
                "mood_boost": (t.get("mode") == "personal"),
                "source": "manual"
            })
            st.success("Completed ✅")
            st.rerun()

def show_mini_calendar(events):
    now = datetime.now()
    end = now + timedelta(days=7)

    parsed = []
    for e in events:
        dt = parse_iso_safe(e.get("start_time"))
        if not dt:
            continue
        if now - timedelta(days=1) <= dt <= end:
            parsed.append((dt, e.get("title", "Untitled")))

    parsed.sort(key=lambda x: x[0])

    grouped = {}
    for dt, title in parsed:
        dkey = dt.strftime("%Y-%m-%d")
        grouped.setdefault(dkey, []).append((dt, title))

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>Mini Calendar</div>", unsafe_allow_html=True)
    st.markdown("<div class='card-sub'>Next 7 days</div>", unsafe_allow_html=True)

    if not grouped:
        st.caption("No upcoming events.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    for dkey, items in grouped.items():
        nice = datetime.fromisoformat(dkey).strftime("%a, %d %b")
        st.markdown(f"**{nice}**")
        for dt, title in items[:6]:
            st.write(f"• {dt.strftime('%H:%M')} — {title}")

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Sidebar
# -----------------------------
def sidebar_nav(stats):
    st.sidebar.markdown("## MoodyBot 3.0")
    st.sidebar.caption("Productivity coach • planner • analytics")

    st.sidebar.markdown("### Mode")
    mode_choice = st.sidebar.radio(
        "Workspace / Personal",
        ["Workspace", "Personal"],
        index=0 if st.session_state.active_mode == "work" else 1,
        horizontal=True
    )
    st.session_state.active_mode = "work" if mode_choice == "Workspace" else "personal"

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Progress")
    st.sidebar.markdown(f"**Level {stats.get('level', 1)}**")
    st.sidebar.progress((stats.get("xp", 0) % 100) / 100)
    st.sidebar.caption(f"🔥 {stats.get('current_streak', 0)} day streak")
    st.sidebar.caption(f"✨ {stats.get('xp', 0)} XP")

    st.sidebar.markdown("---")
    st.session_state.next_best_action = st.sidebar.toggle(
        "Next best action (1 task only)",
        value=st.session_state.next_best_action,
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Dashboard")
    st.session_state.dash_task_limit = st.sidebar.slider(
        "Tasks per bucket", 4, 14, st.session_state.dash_task_limit, 1
    )
    st.session_state.dash_show_completed = st.sidebar.toggle(
        "Show completed", st.session_state.dash_show_completed
    )

    st.sidebar.markdown("---")
    page = st.sidebar.radio(
        "Navigate",
        ["Dashboard", "Tasks", "Schedule", "Analytics", "AI Assistant"],
        index=0,
    )

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Backend: {API_URL}")
    return page

# -----------------------------
# Pages
# -----------------------------
def page_dashboard():
    data = api_get("/dashboard")
    stats = data.get("gamification", {})
    header_bar(stats)

    mode = st.session_state.active_mode

    # Fetch full tasks for clean grouping
    try:
        tasks_all = api_get("/tasks", params={"mode": mode}).get("tasks", [])
    except Exception:
        tasks_all = data.get("tasks", {}).get("tasks", [])

    planned_tasks = [t for t in tasks_all if task_status(t) != "skipped"]
    today_tasks, week_tasks, later_tasks = group_tasks(planned_tasks)
    nba = pick_next_best_action(planned_tasks) if st.session_state.next_best_action else None
    events = data.get("schedule", {}).get("events", [])
    mood = data.get("analytics", {}).get("mood", {})

    # ✅ CLEAN professional layout:
    # Row 1: Quick Add (left wide) + Next Best Action (right)
    # Row 2: Task buckets tabs (left wide) + Right rail: Calendar + AI Coach + Analytics
    top_left, top_right = st.columns([1.6, 1.0], gap="large")

    with top_left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>Quick Add</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-sub'>Add tasks in natural language (keeps auto-add + auto-schedule)</div>", unsafe_allow_html=True)

        with st.form("quick_task", clear_on_submit=True):
            desc = st.text_input("Task", placeholder="I have a customer call in 2 hours, help me prep")
            pr = st.selectbox("Priority", ["low", "medium", "high"], index=1)
            c1, c2, c3 = st.columns([1, 1, 1.2])
            with c1:
                auto_schedule = st.toggle("Auto-schedule", value=True)
            with c2:
                auto_add = st.toggle("Auto-add", value=True)
            with c3:
                submit = st.form_submit_button("Add", use_container_width=True)
            if submit:
                out = send_chat_and_update(desc, mode=mode, auto_add=auto_add, auto_schedule=auto_schedule, default_priority=pr)
                # optional: quick toast-like confirmation
                st.success("Added ✅")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with top_right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>Focus</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-sub'>Your next best action (1 task only)</div>", unsafe_allow_html=True)
        if nba:
            task_row(nba, allow_done_button=True, done_key_prefix="nba_done")
        else:
            st.caption("No pending tasks found. Add one in Quick Add.")
        st.markdown("</div>", unsafe_allow_html=True)

    left, right = st.columns([1.6, 1.0], gap="large")

    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>Planner</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-sub'>Today / This Week / Later • clean buckets with “Show more”</div>", unsafe_allow_html=True)

        limit = st.session_state.dash_task_limit
        tab_today, tab_week, tab_later = st.tabs([
            f"Today ({len(today_tasks)})",
            f"This Week ({len(week_tasks)})",
            f"Later ({len(later_tasks)})"
        ])

        with tab_today:
            if not today_tasks:
                st.caption("Nothing scheduled today.")
            else:
                for t in today_tasks[:limit]:
                    task_row(t, allow_done_button=True, done_key_prefix="today_done")
                if len(today_tasks) > limit:
                    with st.expander(f"Show {len(today_tasks)-limit} more"):
                        for t in today_tasks[limit:]:
                            task_row(t, allow_done_button=True, done_key_prefix="today_more_done")

        with tab_week:
            if not week_tasks:
                st.caption("No scheduled tasks in next 7 days.")
            else:
                for t in week_tasks[:limit]:
                    task_row(t, allow_done_button=True, done_key_prefix="week_done")
                if len(week_tasks) > limit:
                    with st.expander(f"Show {len(week_tasks)-limit} more"):
                        for t in week_tasks[limit:]:
                            task_row(t, allow_done_button=True, done_key_prefix="week_more_done")

        with tab_later:
            if not later_tasks:
                st.caption("No tasks in Later bucket.")
            else:
                for t in later_tasks[:limit]:
                    task_row(t, allow_done_button=True, done_key_prefix="later_done")
                if len(later_tasks) > limit:
                    with st.expander(f"Show {len(later_tasks)-limit} more"):
                        for t in later_tasks[limit:]:
                            task_row(t, allow_done_button=True, done_key_prefix="later_more_done")

        # reprio deltas kept, but tucked away
        if st.session_state.last_reprio:
            st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
            with st.expander("🧠 Auto-reprioritization changes", expanded=False):
                for dlt in st.session_state.last_reprio[:12]:
                    st.write(f"• **{dlt['description']}**")
                    for c in dlt["changes"]:
                        st.caption(c)

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        show_mini_calendar(events)

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>AI Coach</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-sub'>Ask for coping + micro-plan + scheduling</div>", unsafe_allow_html=True)

        text = st.text_area("Ask", height=90, key="dash_ai_text", placeholder="I feel overwhelmed. Help me plan the next 30 minutes.")
        c1, c2 = st.columns([1, 1])
        with c1:
            auto_add = st.toggle("Auto-add", value=True, key="dash_ai_auto_add")
        with c2:
            auto_schedule = st.toggle("Auto-schedule", value=True, key="dash_ai_auto_sched")

        if st.button("Send", key="dash_ai_send", type="primary", use_container_width=True):
            send_chat_and_update(text, mode=mode, auto_add=auto_add, auto_schedule=auto_schedule)
            st.success("Sent ✅")
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>Mood → Productivity</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-sub'>Success rate by mood</div>", unsafe_allow_html=True)
        if mood:
            df = pd.DataFrame({"mood": list(mood.keys()), "success": list(mood.values())})
            st.bar_chart(df.set_index("mood"))
        else:
            st.caption("No analytics yet — complete tasks to generate insights.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        with st.expander("➕ Add Event", expanded=False):
            title = st.text_input("Event title", key="dash_event_title")
            start = st.text_input("Start time (ISO)", datetime.now().isoformat(), key="dash_event_start")
            if st.button("Add to Schedule", key="dash_add_event"):
                api_post("/schedule", {"title": title, "start_time": start})
                st.success("Event added ✅")
                st.rerun()

def page_tasks():
    st.subheader("📝 All Tasks")
    mode = st.selectbox("Filter", ["all", "work", "personal"], key="tasks_filter")
    params = None if mode == "all" else {"mode": mode}
    tasks = api_get("/tasks", params=params).get("tasks", [])

    if st.session_state.last_reprio:
        with st.expander("🧠 Latest auto-reprioritization changes", expanded=False):
            for dlt in st.session_state.last_reprio:
                st.write(f"• **{dlt['description']}**")
                for c in dlt["changes"]:
                    st.caption(c)

    for t in tasks:
        status = task_status(t)
        c1, c2, c3, c4, c5, c6 = st.columns([4.6, 1.6, 2.2, 1.6, 1.6, 1.0])
        with c1:
            new_desc = st.text_input(
                "Task", value=t["description"],
                key=f"desc_{t['id']}", label_visibility="collapsed"
            )
            if status == "done":
                st.caption("✅ Completed")
        with c2:
            st.markdown(priority_badge(t.get("effective_priority")), unsafe_allow_html=True)
        with c3:
            st.caption(f"⏰ {t.get('scheduled_time', 'unscheduled')}")
        with c4:
            if status != "done":
                if st.button("✅ Complete", key=f"complete_{t['id']}"):
                    api_post("/feedback", {
                        "task_id": t["id"],
                        "mood": "neutral",
                        "mode": t.get("mode", "work"),
                        "task_type": "general",
                        "completed": True,
                        "user_priority": t.get("user_priority", "medium"),
                        "mood_boost": (t.get("mode") == "personal"),
                        "source": "manual"
                    })
                    st.rerun()
            else:
                st.button("✅ Done", key=f"done_disabled_{t['id']}", disabled=True)
        with c5:
            if st.button("💾 Save", key=f"save_{t['id']}"):
                api_patch(f"/tasks/{t['id']}", {"description": new_desc})
                st.rerun()
        with c6:
            if st.button("🗑", key=f"del_{t['id']}"):
                api_delete(f"/tasks/{t['id']}")
                st.rerun()

def page_schedule():
    st.subheader("📅 Schedule")
    events = api_get("/schedule").get("events", [])
    show_mini_calendar(events)

    st.markdown("---")
    st.subheader("All Events")

    if not events:
        st.info("No events yet.")

    for e in events:
        c1, c2 = st.columns([6, 1])
        with c1:
            st.write(f"{e.get('start_time')} — {e.get('title')}")
        with c2:
            if st.button("Delete", key=f"ev_{e['id']}"):
                api_delete(f"/schedule/{e['id']}")
                st.rerun()

    with st.expander("➕ Add Event"):
        title = st.text_input("Event title", key="sched_title")
        start = st.text_input("Start time (ISO)", datetime.now().isoformat(), key="sched_start")
        if st.button("Add Event", key="sched_add"):
            api_post("/schedule", {"title": title, "start_time": start})
            st.rerun()

def page_analytics():
    st.subheader("📊 Analytics")

    mood = api_get("/analytics/mood")
    if mood:
        df = pd.DataFrame({"Mood": list(mood.keys()), "Success Rate": list(mood.values())})
        st.line_chart(df.set_index("Mood"))
    else:
        st.info("No analytics yet")

    st.markdown("---")
    st.subheader("📊 Weekly mood → success heatmap (7 days)")
    try:
        weekly = api_get("/analytics/weekly")
        if weekly:
            dfw = pd.DataFrame({"Mood": list(weekly.keys()), "Success": list(weekly.values())})
            st.dataframe(dfw.style.background_gradient(axis=None), use_container_width=True)
        else:
            st.info("No weekly data yet.")
    except Exception:
        st.caption("Weekly endpoint not available yet on backend (/analytics/weekly).")

def page_ai_assistant():
    # Keeping your existing AI page (you already have a better one in your previous version)
    st.subheader("🤖 AI Assistant")
    st.caption("Use the Dashboard for quick add and planning. This is for full chat history.")
    mode = st.session_state.active_mode
    chat_key = "chat_work" if mode == "work" else "chat_personal"
    history = st.session_state[chat_key]

    if history:
        for item in history[-18:]:
            st.markdown(f"**You:** {item['user_text']}")
            st.markdown(f"**MoodyBot:** {item.get('assistant_text','')}")
            st.markdown("---")

    text = st.text_area("Say anything", height=140, key="ai_text")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        auto_add = st.toggle("Auto-add", value=True, key="ai_auto_add")
    with c2:
        auto_schedule = st.toggle("Auto-schedule", value=True, key="ai_auto_sched")
    with c3:
        st.caption("Examples: “I have to call John at 5 PM” → task + schedule. “I feel tired” → suggestions.")

    if st.button("Send", key="ai_send", type="primary"):
        out = send_chat_and_update(text, mode=mode, auto_add=auto_add, auto_schedule=auto_schedule)
        st.session_state[chat_key].append({
            "timestamp": datetime.utcnow().isoformat(),
            "user_text": text,
            "assistant_text": out.get("reply",""),
            "raw": out,
        })
        st.rerun()

# -----------------------------
# Main
# -----------------------------
def main():
    try:
        stats = api_get("/gamification")
        st.session_state.last_stats = stats
    except Exception:
        stats = st.session_state.last_stats

    page = sidebar_nav(stats)

    try:
        if page == "Dashboard":
            page_dashboard()
        elif page == "Tasks":
            page_tasks()
        elif page == "Schedule":
            page_schedule()
        elif page == "Analytics":
            page_analytics()
        else:
            page_ai_assistant()
    except requests.RequestException as e:
        st.error(f"Backend error: {e}")
        st.info(f"Check API URL: {API_URL}")

if __name__ == "__main__":
    main()
