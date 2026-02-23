# app/streamlit_app_notion.py
# 🎨 MoodyBot 3.0 - Notion-Style Professional UI
# Beautiful task management with checkboxes, cards, and modern design

import os
import time
import requests
import streamlit as st
from datetime import datetime, timedelta, timezone
import pandas as pd

# -----------------------------
# Config
# -----------------------------
API_URL = os.getenv("MOODYBOT_API_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(
    page_title="MoodyBot | Task & Mood Manager",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🧠"
)

# -----------------------------
# API helpers
# -----------------------------
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_URL}{path}", params=params, timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return {}

def api_post(path, payload):
    try:
        r = requests.post(f"{API_URL}{path}", json=payload, timeout=220)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return {}

def api_patch(path, payload):
    try:
        r = requests.patch(f"{API_URL}{path}", json=payload, timeout=220)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return {}

def api_delete(path):
    try:
        r = requests.delete(f"{API_URL}{path}", timeout=160)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return {}

# -----------------------------
# State init
# -----------------------------
def init_state():
    defaults = {
        "active_mode": "work",
        "last_stats": {"level": 1, "current_streak": 0, "xp": 0},
        "show_completed": False,
        "view_mode": "board"  # board, list, calendar
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

# -----------------------------
# 🎨 NOTION-STYLE CSS
# -----------------------------
st.markdown("""
<style>
/* Import modern font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* Main container */
.main {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

section.main > div {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Hide Streamlit branding */
#MainMenu, footer, header {visibility: hidden;}

/* Notion-style header */
.notion-header {
    background: white;
    border-radius: 16px;
    padding: 24px 32px;
    margin-bottom: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    border: 1px solid rgba(0,0,0,0.06);
}

.notion-title {
    font-size: 32px;
    font-weight: 700;
    color: #1a202c;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 12px;
}

.notion-subtitle {
    font-size: 14px;
    color: #64748b;
    margin-top: 4px;
}

/* Stats cards (Notion-style) */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
}

.stat-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    border: 1px solid rgba(0,0,0,0.06);
    transition: all 0.2s ease;
}

.stat-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    transform: translateY(-2px);
}

.stat-label {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #64748b;
    margin-bottom: 8px;
}

.stat-value {
    font-size: 28px;
    font-weight: 700;
    color: #1a202c;
    line-height: 1;
}

.stat-hint {
    font-size: 13px;
    color: #94a3b8;
    margin-top: 6px;
}

/* Task card (Notion-style) */
.task-card {
    background: white;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 8px;
    border: 1px solid rgba(0,0,0,0.06);
    transition: all 0.15s ease;
    cursor: pointer;
    display: flex;
    align-items: flex-start;
    gap: 12px;
}

.task-card:hover {
    border-color: rgba(59,130,246,0.3);
    box-shadow: 0 2px 8px rgba(59,130,246,0.08);
}

.task-card.completed {
    opacity: 0.6;
    background: #f8fafc;
}

.task-checkbox {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid #cbd5e1;
    flex-shrink: 0;
    margin-top: 2px;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
}

.task-checkbox:hover {
    border-color: #3b82f6;
    background: rgba(59,130,246,0.05);
}

.task-checkbox.checked {
    background: #3b82f6;
    border-color: #3b82f6;
}

.task-checkbox.checked::after {
    content: '✓';
    color: white;
    font-size: 14px;
    font-weight: 700;
}

.task-content {
    flex: 1;
    min-width: 0;
}

.task-title {
    font-size: 15px;
    font-weight: 500;
    color: #1a202c;
    margin-bottom: 6px;
    line-height: 1.4;
}

.task-card.completed .task-title {
    text-decoration: line-through;
    color: #94a3b8;
}

.task-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    font-size: 12px;
}

.tag {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 500;
    gap: 4px;
}

.tag-priority-high {
    background: #fee2e2;
    color: #991b1b;
}

.tag-priority-medium {
    background: #fef3c7;
    color: #92400e;
}

.tag-priority-low {
    background: #d1fae5;
    color: #065f46;
}

.tag-mode {
    background: #e0e7ff;
    color: #3730a3;
}

.tag-time {
    background: #f3f4f6;
    color: #4b5563;
}

/* Section headers */
.section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 32px 0 16px 0;
    padding-bottom: 8px;
    border-bottom: 2px solid #e2e8f0;
}

.section-title {
    font-size: 18px;
    font-weight: 700;
    color: #1a202c;
    display: flex;
    align-items: center;
    gap: 8px;
}

.section-count {
    background: #f1f5f9;
    color: #64748b;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 13px;
    font-weight: 600;
}

/* Quick add panel */
.quick-add-panel {
    background: white;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
    border: 1px solid rgba(0,0,0,0.06);
}

.quick-add-title {
    font-size: 16px;
    font-weight: 600;
    color: #1a202c;
    margin-bottom: 16px;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 48px 24px;
    color: #94a3b8;
}

.empty-state-icon {
    font-size: 48px;
    margin-bottom: 16px;
    opacity: 0.5;
}

.empty-state-text {
    font-size: 15px;
    color: #64748b;
}

/* Buttons (Notion-style) */
div.stButton > button {
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 14px;
    transition: all 0.2s ease;
}

div.stButton > button:hover {
    background: #2563eb;
    box-shadow: 0 4px 12px rgba(59,130,246,0.3);
    transform: translateY(-1px);
}

/* Text inputs */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    padding: 12px;
    font-size: 14px;
    transition: all 0.2s ease;
}

div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
}

/* View toggle */
.view-toggle {
    background: #f8fafc;
    border-radius: 8px;
    padding: 4px;
    display: inline-flex;
    gap: 4px;
}

.view-toggle-btn {
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    color: #64748b;
    cursor: pointer;
    transition: all 0.2s ease;
}

.view-toggle-btn.active {
    background: white;
    color: #3b82f6;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* Kanban board */
.kanban-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 16px;
    margin-top: 16px;
}

.kanban-column {
    background: #f8fafc;
    border-radius: 12px;
    padding: 16px;
    min-height: 400px;
}

.kanban-column-header {
    font-size: 14px;
    font-weight: 600;
    color: #475569;
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Helper functions
# -----------------------------
def parse_iso_safe(s):
    if not s or s == "unscheduled":
        return None
    try:
        return datetime.fromisoformat(s)
    except:
        return None

def task_status(t):
    return (t.get("status") or "planned").lower()

def is_completed(t):
    return task_status(t) == "done"

def format_time(dt_str):
    """Format datetime string for display"""
    dt = parse_iso_safe(dt_str)
    if not dt:
        return "No date"

    now = datetime.now()
    today = now.date()
    tomorrow = (now + timedelta(days=1)).date()

    if dt.date() == today:
        return f"Today • {dt.strftime('%I:%M %p')}"
    elif dt.date() == tomorrow:
        return f"Tomorrow • {dt.strftime('%I:%M %p')}"
    elif dt.date() < today:
        return f"Overdue • {dt.strftime('%b %d')}"
    else:
        days_diff = (dt.date() - today).days
        if days_diff <= 7:
            return f"{dt.strftime('%A')} • {dt.strftime('%I:%M %p')}"
        return dt.strftime("%b %d • %I:%M %p")

# -----------------------------
# UI Components
# -----------------------------
def render_header(stats):
    """Render Notion-style header"""
    today = datetime.now().strftime("%B %d, %Y")

    st.markdown(f"""
    <div class="notion-header">
        <div class="notion-title">
            🧠 MoodyBot
            <span style="font-size:18px; font-weight:400; color:#94a3b8; margin-left:auto;">
                {today}
            </span>
        </div>
        <div class="notion-subtitle">
            AI-powered task & mood management
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Stats cards
    st.markdown(f"""
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-label">🎯 Level</div>
            <div class="stat-value">{stats.get('level', 1)}</div>
            <div class="stat-hint">Keep growing</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">🔥 Streak</div>
            <div class="stat-value">{stats.get('current_streak', 0)} days</div>
            <div class="stat-hint">Daily consistency</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">✨ XP</div>
            <div class="stat-value">{stats.get('xp', 0)}</div>
            <div class="stat-hint">Experience points</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_task_card(task, key_prefix=""):
    """Render a Notion-style task card with checkbox"""
    task_id = task.get('id')
    title = task.get('description', 'Untitled task')
    priority = task.get('effective_priority', 'medium').lower()
    mode = task.get('mode', 'work')
    scheduled = task.get('scheduled_time', 'unscheduled')
    completed = is_completed(task)

    # Build checkbox HTML
    checkbox_class = "task-checkbox checked" if completed else "task-checkbox"
    card_class = "task-card completed" if completed else "task-card"

    # Priority tag
    priority_html = f'<span class="tag tag-priority-{priority}">⚡ {priority.title()}</span>'

    # Mode tag
    mode_icon = "💼" if mode == "work" else "🏠"
    mode_html = f'<span class="tag tag-mode">{mode_icon} {mode.title()}</span>'

    # Time tag
    time_display = format_time(scheduled)
    time_html = f'<span class="tag tag-time">🕐 {time_display}</span>'

    # Render card
    col1, col2 = st.columns([0.95, 0.05])

    with col1:
        st.markdown(f"""
        <div class="{card_class}">
            <div class="{checkbox_class}" onclick=""></div>
            <div class="task-content">
                <div class="task-title">{title}</div>
                <div class="task-meta">
                    {priority_html}
                    {mode_html}
                    {time_html}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Actual checkbox functionality
        if st.checkbox("", value=completed, key=f"{key_prefix}_{task_id}", label_visibility="collapsed"):
            if not completed:
                # Mark as complete
                api_post("/feedback", {
                    "task_id": task_id,
                    "mood": "neutral",
                    "mode": mode,
                    "task_type": "general",
                    "completed": True,
                    "user_priority": task.get("user_priority", "medium"),
                    "mood_boost": (mode == "personal"),
                    "source": "manual"
                })
                st.rerun()

def render_quick_add():
    """Render quick add task panel"""
    st.markdown('<div class="quick-add-panel">', unsafe_allow_html=True)
    st.markdown('<div class="quick-add-title">➕ Add New Task</div>', unsafe_allow_html=True)

    with st.form("quick_add_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            task_desc = st.text_input("Task description", placeholder="What needs to be done?", label_visibility="collapsed")

        with col2:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=1, label_visibility="collapsed")

        with col3:
            submit = st.form_submit_button("Add Task", use_container_width=True)

        if submit and task_desc.strip():
            mode = st.session_state.active_mode
            result = api_post("/ai/chat", {
                "text": task_desc,
                "default_mode": mode,
                "default_priority": priority,
                "auto_add": True,
                "auto_schedule": True
            })
            if result:
                st.success("✅ Task added!")
                time.sleep(0.5)
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

def render_empty_state(title="No tasks yet", subtitle="Add your first task to get started"):
    """Render empty state"""
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-state-icon">📝</div>
        <div class="empty-state-text">
            <strong>{title}</strong><br>
            {subtitle}
        </div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# Main App
# -----------------------------
def main():
    # Get data
    try:
        stats = api_get("/gamification")
        if not stats:
            stats = {"level": 1, "current_streak": 0, "xp": 0}

        mode = st.session_state.active_mode
        tasks_data = api_get("/tasks", params={"mode": mode})
        all_tasks = tasks_data.get("tasks", [])
    except:
        stats = {"level": 1, "current_streak": 0, "xp": 0}
        all_tasks = []

    # Render header
    render_header(stats)

    # Mode selector
    col1, col2, col3 = st.columns([1, 1, 8])
    with col1:
        if st.button("💼 Work", use_container_width=True, type="primary" if st.session_state.active_mode == "work" else "secondary"):
            st.session_state.active_mode = "work"
            st.rerun()
    with col2:
        if st.button("🏠 Personal", use_container_width=True, type="primary" if st.session_state.active_mode == "personal" else "secondary"):
            st.session_state.active_mode = "personal"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Quick add
    render_quick_add()

    # Group tasks
    show_completed = st.checkbox("Show completed tasks", value=st.session_state.get("show_completed", False))
    st.session_state.show_completed = show_completed

    pending_tasks = [t for t in all_tasks if not is_completed(t)]
    completed_tasks = [t for t in all_tasks if is_completed(t)]

    now = datetime.now()
    today = now.date()
    week_end = now + timedelta(days=7)

    # Categorize pending tasks
    today_tasks = []
    upcoming_tasks = []
    later_tasks = []

    for task in pending_tasks:
        dt = parse_iso_safe(task.get("scheduled_time"))
        if dt is None:
            later_tasks.append(task)
        elif dt.date() == today:
            today_tasks.append(task)
        elif dt.date() <= week_end.date():
            upcoming_tasks.append(task)
        else:
            later_tasks.append(task)

    # Sort by time
    today_tasks.sort(key=lambda t: parse_iso_safe(t.get("scheduled_time")) or datetime.max)
    upcoming_tasks.sort(key=lambda t: parse_iso_safe(t.get("scheduled_time")) or datetime.max)

    # Render sections
    st.markdown(f"""
    <div class="section-header">
        <div class="section-title">
            📅 Today
            <span class="section-count">{len(today_tasks)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if today_tasks:
        for task in today_tasks:
            render_task_card(task, "today")
    else:
        render_empty_state("No tasks for today", "You're all caught up!")

    st.markdown(f"""
    <div class="section-header">
        <div class="section-title">
            📆 This Week
            <span class="section-count">{len(upcoming_tasks)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if upcoming_tasks:
        for task in upcoming_tasks:
            render_task_card(task, "upcoming")
    else:
        render_empty_state("No upcoming tasks", "Plan ahead for the week")

    st.markdown(f"""
    <div class="section-header">
        <div class="section-title">
            📋 Later
            <span class="section-count">{len(later_tasks)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if later_tasks:
        for task in later_tasks:
            render_task_card(task, "later")
    else:
        render_empty_state("No backlog tasks", "All clear!")

    # Completed section
    if show_completed and completed_tasks:
        st.markdown(f"""
        <div class="section-header">
            <div class="section-title">
                ✅ Completed
                <span class="section-count">{len(completed_tasks)}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        for task in completed_tasks[:10]:  # Show max 10 completed
            render_task_card(task, "completed")

if __name__ == "__main__":
    main()
