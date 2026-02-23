# app/streamlit_app_pro.py
# 🎨 MoodyBot 3.0 - Professional Notion-Style UI with AI Chat
# Beautiful task management + AI Chat Window + Smart Colors

import os
import time
import requests
import streamlit as st
from datetime import datetime, timedelta, timezone
import pandas as pd

# Import analytics page renderer
try:
    from analytics_page import render_analytics_page
except ImportError:
    render_analytics_page = None

# -----------------------------
# Config
# -----------------------------
API_URL = os.getenv("MOODYBOT_API_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(
    page_title="MoodyBot | AI Task Manager",
    layout="wide",
    initial_sidebar_state="expanded",
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
        "active_page": "tasks",  # tasks, chat, analytics
        "chat_history": [],
        "theme": "light"  # light or dark
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

# -----------------------------
# 🎨 SMART COLOR SYSTEM
# -----------------------------
def get_theme_colors():
    """Smart color system that adapts to light/dark mode"""
    if st.session_state.get("theme") == "dark":
        return {
            "bg_primary": "#1a1a1a",
            "bg_secondary": "#2d2d2d",
            "bg_card": "#252525",
            "text_primary": "#e5e5e5",
            "text_secondary": "#a0a0a0",
            "text_muted": "#707070",
            "border": "rgba(255,255,255,0.1)",
            "accent": "#3b82f6",
            "accent_hover": "#2563eb",
            "success": "#10b981",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "shadow": "0 2px 8px rgba(0,0,0,0.3)",
        }
    else:
        return {
            "bg_primary": "#ffffff",
            "bg_secondary": "#f8fafc",
            "bg_card": "#ffffff",
            "text_primary": "#1a202c",
            "text_secondary": "#64748b",
            "text_muted": "#94a3b8",
            "border": "rgba(0,0,0,0.08)",
            "accent": "#3b82f6",
            "accent_hover": "#2563eb",
            "success": "#10b981",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "shadow": "0 2px 8px rgba(0,0,0,0.1)",
        }

colors = get_theme_colors()

# -----------------------------
# 🎨 ENHANCED CSS WITH SMART COLORS
# -----------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}}

.main {{
    background: {colors['bg_secondary']};
}}

section.main > div {{
    padding-top: 1rem;
    padding-bottom: 2rem;
}}

#MainMenu, footer, header {{visibility: hidden;}}

/* Notion-style header */
.notion-header {{
    background: {colors['bg_card']};
    border-radius: 16px;
    padding: 24px 32px;
    margin-bottom: 20px;
    box-shadow: {colors['shadow']};
    border: 1px solid {colors['border']};
}}

.notion-title {{
    font-size: 32px;
    font-weight: 700;
    color: {colors['text_primary']};
    margin: 0;
    display: flex;
    align-items: center;
    gap: 12px;
}}

.notion-subtitle {{
    font-size: 14px;
    color: {colors['text_secondary']};
    margin-top: 4px;
}}

/* Stats cards */
.stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    margin-bottom: 20px;
}}

.stat-card {{
    background: {colors['bg_card']};
    border-radius: 12px;
    padding: 20px;
    border: 1px solid {colors['border']};
    transition: all 0.2s ease;
}}

.stat-card:hover {{
    box-shadow: {colors['shadow']};
    transform: translateY(-2px);
    border-color: {colors['accent']};
}}

.stat-label {{
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: {colors['text_secondary']};
    margin-bottom: 8px;
}}

.stat-value {{
    font-size: 28px;
    font-weight: 700;
    color: {colors['text_primary']};
    line-height: 1;
}}

.stat-hint {{
    font-size: 12px;
    color: {colors['text_muted']};
    margin-top: 6px;
}}

/* Navigation tabs */
.nav-tabs {{
    display: flex;
    gap: 8px;
    margin-bottom: 20px;
    padding: 4px;
    background: {colors['bg_secondary']};
    border-radius: 12px;
    border: 1px solid {colors['border']};
}}

.nav-tab {{
    flex: 1;
    padding: 12px 20px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    color: {colors['text_secondary']};
    text-align: center;
    cursor: pointer;
    transition: all 0.2s ease;
    border: none;
    background: transparent;
}}

.nav-tab:hover {{
    background: {colors['bg_card']};
    color: {colors['text_primary']};
}}

.nav-tab.active {{
    background: {colors['accent']};
    color: white;
    box-shadow: {colors['shadow']};
}}

/* Task card */
.task-card {{
    background: {colors['bg_card']};
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 8px;
    border: 1px solid {colors['border']};
    transition: all 0.15s ease;
    cursor: pointer;
    display: flex;
    align-items: flex-start;
    gap: 14px;
}}

.task-card:hover {{
    border-color: {colors['accent']};
    box-shadow: {colors['shadow']};
    transform: translateX(4px);
}}

.task-card.completed {{
    opacity: 0.6;
    background: {colors['bg_secondary']};
}}

.task-checkbox {{
    width: 22px;
    height: 22px;
    border-radius: 6px;
    border: 2px solid {colors['text_muted']};
    flex-shrink: 0;
    margin-top: 2px;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.task-checkbox:hover {{
    border-color: {colors['accent']};
    background: rgba(59,130,246,0.1);
}}

.task-checkbox.checked {{
    background: {colors['accent']};
    border-color: {colors['accent']};
}}

.task-checkbox.checked::after {{
    content: '✓';
    color: white;
    font-size: 14px;
    font-weight: 700;
}}

.task-content {{
    flex: 1;
    min-width: 0;
}}

.task-title {{
    font-size: 15px;
    font-weight: 500;
    color: {colors['text_primary']};
    margin-bottom: 8px;
    line-height: 1.5;
}}

.task-card.completed .task-title {{
    text-decoration: line-through;
    color: {colors['text_muted']};
}}

.task-meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    font-size: 12px;
}}

.tag {{
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    gap: 4px;
}}

.tag-priority-high {{
    background: #fee2e2;
    color: #991b1b;
}}

.tag-priority-medium {{
    background: #fef3c7;
    color: #92400e;
}}

.tag-priority-low {{
    background: #d1fae5;
    color: #065f46;
}}

.tag-mode {{
    background: #e0e7ff;
    color: #3730a3;
}}

.tag-time {{
    background: {colors['bg_secondary']};
    color: {colors['text_secondary']};
    border: 1px solid {colors['border']};
}}

/* Section headers */
.section-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 28px 0 12px 0;
    padding-bottom: 10px;
    border-bottom: 2px solid {colors['border']};
}}

.section-title {{
    font-size: 18px;
    font-weight: 700;
    color: {colors['text_primary']};
    display: flex;
    align-items: center;
    gap: 8px;
}}

.section-count {{
    background: {colors['bg_secondary']};
    color: {colors['text_secondary']};
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 13px;
    font-weight: 600;
    border: 1px solid {colors['border']};
}}

/* Chat interface */
.chat-container {{
    background: {colors['bg_card']};
    border-radius: 12px;
    padding: 0;
    border: 1px solid {colors['border']};
    height: 600px;
    display: flex;
    flex-direction: column;
}}

.chat-header {{
    padding: 16px 20px;
    border-bottom: 1px solid {colors['border']};
    font-weight: 600;
    color: {colors['text_primary']};
}}

.chat-messages {{
    flex: 1;
    overflow-y: auto;
    padding: 20px;
}}

.chat-message {{
    margin-bottom: 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
}}

.chat-message.user {{
    align-items: flex-end;
}}

.chat-message.assistant {{
    align-items: flex-start;
}}

.message-bubble {{
    max-width: 70%;
    padding: 12px 16px;
    border-radius: 12px;
    font-size: 14px;
    line-height: 1.5;
}}

.message-bubble.user {{
    background: {colors['accent']};
    color: white;
    border-bottom-right-radius: 4px;
}}

.message-bubble.assistant {{
    background: {colors['bg_secondary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    border-bottom-left-radius: 4px;
}}

.message-label {{
    font-size: 11px;
    font-weight: 600;
    color: {colors['text_muted']};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.chat-input-area {{
    padding: 16px 20px;
    border-top: 1px solid {colors['border']};
    background: {colors['bg_secondary']};
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
}}

/* Quick add panel */
.quick-add-panel {{
    background: {colors['bg_card']};
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    border: 1px solid {colors['border']};
}}

.quick-add-title {{
    font-size: 15px;
    font-weight: 600;
    color: {colors['text_primary']};
    margin-bottom: 12px;
}}

/* Empty state */
.empty-state {{
    text-align: center;
    padding: 48px 24px;
    color: {colors['text_muted']};
}}

.empty-state-icon {{
    font-size: 48px;
    margin-bottom: 12px;
    opacity: 0.6;
}}

.empty-state-text {{
    font-size: 14px;
    color: {colors['text_secondary']};
}}

/* Buttons */
div.stButton > button {{
    background: {colors['accent']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 14px;
    transition: all 0.2s ease;
    width: 100%;
}}

div.stButton > button:hover {{
    background: {colors['accent_hover']};
    box-shadow: {colors['shadow']};
    transform: translateY(-1px);
}}

/* Text inputs */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {{
    border-radius: 8px;
    border: 1px solid {colors['border']};
    background: {colors['bg_card']};
    color: {colors['text_primary']};
    padding: 12px;
    font-size: 14px;
    transition: all 0.2s ease;
}}

div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {{
    border-color: {colors['accent']};
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
}}

/* Selectbox */
div[data-testid="stSelectbox"] {{
    background: {colors['bg_card']};
}}

/* Mode toggle buttons */
.stButton > button[kind="secondary"] {{
    background: {colors['bg_secondary']};
    color: {colors['text_secondary']};
    border: 1px solid {colors['border']};
}}

.stButton > button[kind="primary"] {{
    background: {colors['accent']};
    color: white;
}}
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
    today = datetime.now().strftime("%B %d, %Y")

    st.markdown(f"""
    <div class="notion-header">
        <div class="notion-title">
            🧠 MoodyBot
            <span style="font-size:16px; font-weight:400; color:{colors['text_secondary']}; margin-left:auto;">
                {today}
            </span>
        </div>
        <div class="notion-subtitle">
            AI-powered task & mood management • Chat with your assistant
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-label">🎯 LEVEL</div>
            <div class="stat-value">{stats.get('level', 1)}</div>
            <div class="stat-hint">Keep growing</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">🔥 STREAK</div>
            <div class="stat-value">{stats.get('current_streak', 0)}</div>
            <div class="stat-hint">Day{'' if stats.get('current_streak', 0) == 1 else 's'}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">✨ XP POINTS</div>
            <div class="stat-value">{stats.get('xp', 0)}</div>
            <div class="stat-hint">Total earned</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_navigation():
    """Render navigation tabs"""
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📋 Tasks", use_container_width=True, type="primary" if st.session_state.active_page == "tasks" else "secondary"):
            st.session_state.active_page = "tasks"
            st.rerun()

    with col2:
        if st.button("💬 AI Chat", use_container_width=True, type="primary" if st.session_state.active_page == "chat" else "secondary"):
            st.session_state.active_page = "chat"
            st.rerun()

    with col3:
        if st.button("📊 Analytics", use_container_width=True, type="primary" if st.session_state.active_page == "analytics" else "secondary"):
            st.session_state.active_page = "analytics"
            st.rerun()

def render_task_card(task, key_prefix=""):
    task_id = task.get('id')
    title = task.get('description', 'Untitled task')
    priority = task.get('effective_priority', 'medium').lower()
    mode = task.get('mode', 'work')
    scheduled = task.get('scheduled_time', 'unscheduled')
    completed = is_completed(task)

    checkbox_class = "task-checkbox checked" if completed else "task-checkbox"
    card_class = "task-card completed" if completed else "task-card"

    priority_html = f'<span class="tag tag-priority-{priority}">⚡ {priority.title()}</span>'
    mode_icon = "💼" if mode == "work" else "🏠"
    mode_html = f'<span class="tag tag-mode">{mode_icon} {mode.title()}</span>'
    time_display = format_time(scheduled)
    time_html = f'<span class="tag tag-time">🕐 {time_display}</span>'

    col1, col2 = st.columns([0.95, 0.05])

    with col1:
        st.markdown(f"""
        <div class="{card_class}">
            <div class="{checkbox_class}"></div>
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
        if st.checkbox("", value=completed, key=f"{key_prefix}_{task_id}", label_visibility="collapsed"):
            if not completed:
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
    st.markdown(f'<div class="quick-add-panel">', unsafe_allow_html=True)
    st.markdown(f'<div class="quick-add-title">➕ Quick Add Task</div>', unsafe_allow_html=True)

    with st.form("quick_add_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            task_desc = st.text_input("", placeholder="What needs to be done?", label_visibility="collapsed")

        with col2:
            priority = st.selectbox("", ["low", "medium", "high"], index=1, label_visibility="collapsed")

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
                st.success("✅ Task added successfully!")
                time.sleep(0.5)
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

def render_chat_interface():
    """Render AI Chat interface"""
    # Build entire chat HTML as single string
    chat_html = """
    <div class="chat-container">
        <div class="chat-header">
            💬 Chat with MoodyBot AI Assistant
        </div>
        <div class="chat-messages" id="chat-messages">
    """

    # Display chat history
    chat_history = st.session_state.get("chat_history", [])

    if not chat_history:
        chat_html += """
            <div class="empty-state">
                <div class="empty-state-icon">💬</div>
                <div class="empty-state-text">
                    Start a conversation with your AI assistant<br>
                    Ask about tasks, get mood support, or schedule help
                </div>
            </div>
        """
    else:
        for msg in chat_history[-10:]:  # Show last 10 messages
            msg_type = msg.get("type", "user")
            content = msg.get("content", "").replace("<", "&lt;").replace(">", "&gt;")
            label = 'You' if msg_type == 'user' else 'MoodyBot AI'

            chat_html += f"""
            <div class="chat-message {msg_type}">
                <div class="message-label">{label}</div>
                <div class="message-bubble {msg_type}">
                    {content}
                </div>
            </div>
            """

    chat_html += """
        </div>
    </div>
    """

    st.markdown(chat_html, unsafe_allow_html=True)

    # Chat input
    st.markdown("<br>", unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])

        with col1:
            user_input = st.text_area("Message", placeholder="Ask me anything... (e.g., 'I feel overwhelmed, help me prioritize')", height=100, label_visibility="collapsed")

        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            send_btn = st.form_submit_button("Send 💬", use_container_width=True)

        if send_btn and user_input.strip():
            # Add user message
            st.session_state.chat_history.append({
                "type": "user",
                "content": user_input,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            # Get AI response
            mode = st.session_state.active_mode
            result = api_post("/ai/chat", {
                "text": user_input,
                "default_mode": mode,
                "default_priority": "medium",
                "auto_add": True,
                "auto_schedule": True
            })

            if result:
                reply = result.get("reply", "I'm here to help! How can I assist you?")
                st.session_state.chat_history.append({
                    "type": "assistant",
                    "content": reply,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

                # Show created tasks
                created_tasks = result.get("auto_added", []) or result.get("created_tasks", [])
                if created_tasks:
                    task_list = "<br>".join([f"• {t.get('description', 'Task')}" for t in created_tasks[:3]])
                    st.session_state.chat_history.append({
                        "type": "assistant",
                        "content": f"✅ Created {len(created_tasks)} task(s):<br>{task_list}",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })

            st.rerun()

def render_empty_state(title="No tasks yet", subtitle="Add your first task to get started"):
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
# Pages
# -----------------------------
def page_tasks():
    """Tasks page"""
    # Mode selector
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💼 Work Mode", use_container_width=True, type="primary" if st.session_state.active_mode == "work" else "secondary"):
            st.session_state.active_mode = "work"
            st.rerun()
    with col2:
        if st.button("🏠 Personal Mode", use_container_width=True, type="primary" if st.session_state.active_mode == "personal" else "secondary"):
            st.session_state.active_mode = "personal"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Quick add
    render_quick_add()

    # Get tasks
    mode = st.session_state.active_mode
    tasks_data = api_get("/tasks", params={"mode": mode})
    all_tasks = tasks_data.get("tasks", [])

    # Filter
    show_completed = st.checkbox("Show completed tasks", value=st.session_state.get("show_completed", False))
    st.session_state.show_completed = show_completed

    pending_tasks = [t for t in all_tasks if not is_completed(t)]
    completed_tasks = [t for t in all_tasks if is_completed(t)]

    # Group by date
    now = datetime.now()
    today = now.date()
    week_end = now + timedelta(days=7)

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
        render_empty_state("No tasks for today", "You're all clear! ✨")

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
        render_empty_state("No upcoming tasks", "Plan ahead for success")

    st.markdown(f"""
    <div class="section-header">
        <div class="section-title">
            📋 Backlog
            <span class="section-count">{len(later_tasks)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if later_tasks:
        for task in later_tasks:
            render_task_card(task, "later")
    else:
        render_empty_state("No backlog", "All organized!")

    if show_completed and completed_tasks:
        st.markdown(f"""
        <div class="section-header">
            <div class="section-title">
                ✅ Completed
                <span class="section-count">{len(completed_tasks)}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        for task in completed_tasks[:10]:
            render_task_card(task, "completed")

def page_chat():
    """Chat page"""
    render_chat_interface()

def page_analytics():
    """Analytics page with advanced visualizations"""
    st.markdown(f"""
    <div class="section-header">
        <div class="section-title">📊 Analytics & Insights</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        # Use the new advanced analytics if available
        if render_analytics_page:
            # Get comprehensive dashboard data
            dashboard_data = api_get("/analytics/dashboard-data")

            if dashboard_data and 'error' not in dashboard_data:
                render_analytics_page(dashboard_data)
            elif dashboard_data and 'fallback' in dashboard_data:
                # Fallback to simple analytics
                st.warning("Advanced analytics unavailable. Showing basic analytics.")
                _render_simple_analytics()
            else:
                _render_simple_analytics()
        else:
            _render_simple_analytics()

    except Exception as e:
        st.error(f"Analytics error: {str(e)}")
        _render_simple_analytics()

def _render_simple_analytics():
    """Fallback simple analytics view"""
    try:
        mood_data = api_get("/analytics/mood")

        if mood_data:
            st.subheader("Mood → Productivity Correlation")
            df = pd.DataFrame({
                "Mood": list(mood_data.keys()),
                "Success Rate": [v * 100 for v in mood_data.values()]
            })
            st.bar_chart(df.set_index("Mood"))
        else:
            render_empty_state("No analytics yet", "Complete tasks to see insights")
    except:
        render_empty_state("Analytics unavailable", "Start using MoodyBot to generate data")

# -----------------------------
# Main App
# -----------------------------
def main():
    try:
        stats = api_get("/gamification")
        if not stats:
            stats = {"level": 1, "current_streak": 0, "xp": 0}
    except:
        stats = {"level": 1, "current_streak": 0, "xp": 0}

    render_header(stats)
    render_navigation()

    st.markdown("<br>", unsafe_allow_html=True)

    # Route to active page
    if st.session_state.active_page == "tasks":
        page_tasks()
    elif st.session_state.active_page == "chat":
        page_chat()
    elif st.session_state.active_page == "analytics":
        page_analytics()

if __name__ == "__main__":
    main()
