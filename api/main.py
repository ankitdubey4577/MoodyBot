# api/main.py
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import func

from src.graph.moodybot_graph import MoodyBotGraph
from src.db.database import SessionLocal
from src.db.models import Task, Event, TaskFeedback, UserStats
from src.utils.gamification import update_streak, calculate_xp, get_level
from src.agents.analytics_agent import mood_productivity
from src.agents.sentiment_agent import analyze_sentiment
from src.utils.date_parser import parse_natural_datetime


# Optional LLM

try:
    from langchain_community.llms import Ollama
except Exception:
    Ollama = None


# App

app = FastAPI(title="MoodyBot Enterprise API")
graph = MoodyBotGraph()

_llm = Ollama(model="llama3", temperature=0.25, num_predict=320) if Ollama else None


# DB

def db():
    return SessionLocal()

# LLM JSON helper (SAFE)
def llm_ask_json(prompt: str, retries: int = 2) -> Optional[Dict[str, Any]]:
    if _llm is None:
        return None

    for _ in range(max(1, retries)):
        try:
            raw = _llm.invoke(prompt)
            text = raw if isinstance(raw, str) else str(raw)

            m = re.search(r"\{[\s\S]*\}", text)
            if not m:
                continue

            blob = m.group(0)
            try:
                return json.loads(blob)
            except Exception:
                # try a quick cleanup
                blob2 = re.sub(r",\s*}", "}", blob)
                blob2 = re.sub(r",\s*]", "]", blob2)
                try:
                    return json.loads(blob2)
                except Exception:
                    continue
        except Exception:
            continue

    return None

# Schemas
class ChatIn(BaseModel):
    text: str
    default_mode: str = "work"
    default_priority: str = "medium"
    auto_add: bool = True
    auto_schedule: bool = True

class TaskCreate(BaseModel):
    description: str
    user_priority: str = "medium"
    scheduled_time: Optional[str] = None
    mode: str = "work"

class TaskUpdate(BaseModel):
    description: Optional[str] = None
    user_priority: Optional[str] = None
    scheduled_time: Optional[str] = None
    status: Optional[str] = None

class EventCreate(BaseModel):
    title: str
    start_time: str

class FeedbackIn(BaseModel):
    task_id: int
    mood: str
    mode: str
    task_type: str = "general"
    completed: bool
    user_priority: str = "medium"
    mood_boost: bool = False
    source: str = "manual"
    # optional fields that may exist in your DB model:
    time_taken: Optional[int] = None
    time_of_day: Optional[str] = None


# Intent detection (ADD_TASK vs CHAT vs SCHEDULE)

_INTENT_ADD = re.compile(r"\b(add|create)\b.*\b(task|todo)\b", re.I)
_INTENT_SCHED = re.compile(
    r"\b(i have to|i need to|remind me|call|meet|meeting|appointment|schedule)\b",
    re.I,
)

def detect_intent(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return "CHAT"
    if _INTENT_ADD.search(t):
        return "ADD_TASK"
    if _INTENT_SCHED.search(t):
        return "SCHEDULE"
    return "CHAT"


# CLEAN task extraction + splitting

_ACTION_VERBS = {
    "call","meet","email","message","prepare","prep","review","send",
    "finish","complete","submit","write","plan","check","fix","update",
    "join","follow","book","pay","refactor","test","deploy","debug",
    "nap","rest"
}

_BAD_TITLES = {"task","todo","something","do task","work","meeting"}

_NAP_WORDS = {"nap","power nap","sleep","rest"}

def clean_title(t: str) -> str:
    t = t.strip()
    # strip leading intent fluff
    t = re.sub(
        r"^(please\s+)?(i have to|i need to|i should|remind me to|add|create)\s+",
        "",
        t,
        flags=re.I,
    )
    t = t.strip(" .,-")
    t = re.sub(r"\s+", " ", t)
    return t[:160]

def split_compound_tasks(text: str) -> List[str]:
    """
    Split compound sentences into multiple tasks.
    Keeps only action-like chunks.
    """
    if not text or not text.strip():
        return []

    # Split on conjunctions / punctuation but keep meaningful phrases
    parts = re.split(r"\b(?:and then|then|and also|also|but|;|\.|\n)\b", text, flags=re.I)
    tasks: List[str] = []

    for p in parts:
        p = clean_title(p)
        if len(p) < 4:
            continue
        pl = p.lower()
        if pl in _BAD_TITLES:
            continue
        if not any(v in pl for v in _ACTION_VERBS):
            continue
        tasks.append(p)

    # if nothing matched but intent was task-ish, fallback to cleaned whole line
    return tasks[:5] if tasks else [clean_title(text)]

def confidence_for_title(title: str) -> float:
    """
    Confidence scoring to suppress auto-add when unsure.
    """
    t = (title or "").lower().strip()
    if not t or t in _BAD_TITLES:
        return 0.0

    score = 0.35

    # has action
    if any(v in t for v in _ACTION_VERBS):
        score += 0.35

    # has time cue or specificity
    if any(x in t for x in [" at ", " pm", " am", "today", "tomorrow", "in ", "before ", "after "]):
        score += 0.15

    # length sanity
    if len(t) < 8:
        score -= 0.20
    if len(t) > 120:
        score -= 0.10

    # penalize vague emotional-only
    if re.fullmatch(r"(i\s*(am|'m)\s*)?(sad|down|tired|anxious|stressed|overwhelmed)\b.*", t):
        score -= 0.35

    return max(0.0, min(score, 0.95))


# Scheduling helpers
# - Event duration = duration_min (encoded in event title)
# - Avoid naps near meetings

_DUR_TAG = re.compile(r"\((\d+)\s*m\)", re.I)

_MEETING_HINTS = {"meeting","call","sync","standup","interview","demo","appointment","review"}

def _parse_iso(s: Optional[str]) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(s) if s and s != "unscheduled" else None
    except Exception:
        return None

def _round_block(dt: datetime, block: int) -> datetime:
    dt = dt.replace(second=0, microsecond=0)
    r = dt.minute % block
    return dt if r == 0 else dt + timedelta(minutes=(block - r))

def is_meeting_title(title: str) -> bool:
    tl = (title or "").lower()
    return any(w in tl for w in _MEETING_HINTS)

def is_nap_task(title: str) -> bool:
    tl = (title or "").lower()
    return any(w in tl for w in _NAP_WORDS)

def duration_from_event_title(title: str, default_min: int = 30) -> int:
    """
    Event duration is encoded like: "... (15m): ..."
    """
    if not title:
        return default_min
    m = _DUR_TAG.search(title)
    if not m:
        return default_min
    try:
        v = int(m.group(1))
        return max(5, min(v, 240))
    except Exception:
        return default_min

def find_next_available_slot(
    events: List[Dict[str, Any]],
    after: Optional[datetime] = None,
    block: int = 15,
    duration_min: int = 30,
    avoid_meeting_buffer_for_naps_min: int = 20,
    avoid_naps: bool = False,
) -> str:
    """
    Finds next free slot avoiding event overlaps.
    If avoid_naps=True, also avoid scheduling inside "meeting buffers" (not right before/after meetings).
    """
    now = after or datetime.now()
    candidate = _round_block(now + timedelta(minutes=1), block)

    busy: List[Tuple[datetime, datetime, str]] = []
    for e in events:
        st = _parse_iso(e.get("start_time"))
        if not st:
            continue
        title = e.get("title", "")
        dur = duration_from_event_title(title, default_min=30)
        busy.append((st, st + timedelta(minutes=dur), title))

    busy.sort(key=lambda x: x[0])

    horizon = now + timedelta(hours=12)

    while candidate < horizon:
        end = candidate + timedelta(minutes=duration_min)

        # basic overlap avoid
        collision = False
        for b0, b1, _title in busy:
            if end > b0 and candidate < b1:
                collision = True
                candidate = _round_block(b1 + timedelta(minutes=1), block)
                break
        if collision:
            continue

        # nap rule: avoid too close to meetings
        if avoid_naps:
            bad = False
            for b0, b1, ttl in busy:
                if not is_meeting_title(ttl):
                    continue
                # buffer around meeting
                buf0 = b0 - timedelta(minutes=avoid_meeting_buffer_for_naps_min)
                buf1 = b1 + timedelta(minutes=avoid_meeting_buffer_for_naps_min)
                if end > buf0 and candidate < buf1:
                    bad = True
                    candidate = _round_block(buf1 + timedelta(minutes=1), block)
                    break
            if bad:
                continue

        return candidate.isoformat()

    return _round_block(horizon, block).isoformat()

def ensure_no_conflict(
    desired_iso: Optional[str],
    events: List[Dict[str, Any]],
    duration_min: int,
    avoid_naps: bool,
) -> Tuple[str, bool]:
    """
    If desired time overlaps, shift to next available slot.
    Returns (final_iso, changed)
    """
    desired = _parse_iso(desired_iso) if desired_iso else None
    if desired is None:
        # pick next slot
        return (
            find_next_available_slot(
                events,
                after=datetime.now(),
                duration_min=duration_min,
                avoid_naps=avoid_naps,
            ),
            True,
        )

    # check desired overlap
    cand = desired
    end = cand + timedelta(minutes=duration_min)

    busy: List[Tuple[datetime, datetime, str]] = []
    for e in events:
        st = _parse_iso(e.get("start_time"))
        if not st:
            continue
        title = e.get("title", "")
        dur = duration_from_event_title(title, default_min=30)
        busy.append((st, st + timedelta(minutes=dur), title))
    busy.sort(key=lambda x: x[0])

    # overlap?
    for b0, b1, _title in busy:
        if end > b0 and cand < b1:
            # shift
            new_iso = find_next_available_slot(
                events,
                after=cand,
                duration_min=duration_min,
                avoid_naps=avoid_naps,
            )
            return new_iso, True

    # nap buffer check
    if avoid_naps:
        for b0, b1, ttl in busy:
            if not is_meeting_title(ttl):
                continue
            buf0 = b0 - timedelta(minutes=20)
            buf1 = b1 + timedelta(minutes=20)
            if end > buf0 and cand < buf1:
                new_iso = find_next_available_slot(
                    events,
                    after=cand,
                    duration_min=duration_min,
                    avoid_naps=True,
                )
                return new_iso, True

    return desired.replace(second=0, microsecond=0).isoformat(), False

def staggered_slots(
    events: List[Dict[str, Any]],
    base: datetime,
    offsets_min: List[int],
    duration_min: int,
    avoid_naps: bool,
) -> List[str]:
    """
    Teach the LLM to return multiple staggered time slots:
    We will compute slots at offsets and dedupe.
    """
    slots: List[str] = []
    for off in offsets_min:
        slot = find_next_available_slot(
            events,
            after=base + timedelta(minutes=int(off)),
            duration_min=duration_min,
            avoid_naps=avoid_naps,
        )
        if slot not in slots:
            slots.append(slot)
    return slots[:5]


# Task <-> Event linkage (no DB schema change)
# - Encode duration in Event.title

def event_title_for_task(task_id: int, task_title: str, duration_min: int) -> str:
    # format: Task#123 (15m): Do thing
    safe_title = (task_title or "").strip()
    safe_title = re.sub(r"\s+", " ", safe_title)
    safe_title = safe_title[:140]
    return f"Task#{task_id} ({int(duration_min)}m): {safe_title}"

def find_event_for_task(d, task_id: int) -> Optional[Event]:
    return d.query(Event).filter(Event.title.like(f"Task#{task_id} %")).first()


# DB helpers

def task_to_dict(t: Task) -> Dict[str, Any]:
    return {
        "id": t.id,
        "description": getattr(t, "title", None),
        "mode": getattr(t, "mode", None),
        "user_priority": getattr(t, "user_priority", None),
        "ai_priority": getattr(t, "ai_priority", None),
        "effective_priority": getattr(t, "effective_priority", getattr(t, "user_priority", None)),
        "scheduled_time": getattr(t, "scheduled_time", None),
        "status": getattr(t, "status", "planned"),
        "deadline": getattr(t, "deadline", None),
        "ai_reason": getattr(t, "ai_priority_reason", None),
        "created_at": getattr(t, "created_at", None).isoformat() if getattr(t, "created_at", None) else None,
    }

def event_to_dict(e: Event) -> Dict[str, Any]:
    return {
        "id": e.id,
        "title": e.title,
        "start_time": e.start_time,
        "created_at": getattr(e, "created_at", None).isoformat() if getattr(e, "created_at", None) else None,
        "duration_min": duration_from_event_title(getattr(e, "title", ""), default_min=30),
    }

def create_task_db(desc: str, mode: str, pr: str, sched: Optional[str], duration_min: int = 30) -> Dict[str, Any]:
    """
    Creates task and (if scheduled) creates corresponding event with duration embedded.
    """
    d = db()
    try:
        t = Task(
            title=desc,
            mode=mode,
            user_priority=pr,
            effective_priority=pr,
            scheduled_time=sched or "unscheduled",
            created_at=datetime.utcnow(),
        )
        if hasattr(t, "status"):
            t.status = "planned"
        if hasattr(t, "ai_priority_reason"):
            t.ai_priority_reason = None

        d.add(t)
        d.commit()
        d.refresh(t)

        calendar_ops: List[Dict[str, Any]] = []

        if sched and sched != "unscheduled":
            ev = Event(
                title=event_title_for_task(t.id, t.title, duration_min),
                start_time=sched,
                created_at=datetime.utcnow(),
            )
            d.add(ev)
            d.commit()
            d.refresh(ev)
            calendar_ops.append({"op": "event_created", "task_id": t.id, "event_id": ev.id, "start_time": ev.start_time, "title": ev.title})

        out = task_to_dict(t)
        if calendar_ops:
            out["_calendar_ops"] = calendar_ops
        return out
    finally:
        d.close()

def sync_task_event_on_update(d, task_obj: Task, duration_min: int = 30) -> List[Dict[str, Any]]:
    """
    Auto-update calendar on task edit:
    - If scheduled_time becomes scheduled => create/update event
    - If scheduled_time becomes unscheduled => delete event
    - If title changes => update event title
    """
    ops: List[Dict[str, Any]] = []
    ev = find_event_for_task(d, task_obj.id)

    stime = getattr(task_obj, "scheduled_time", None)
    is_sched = bool(stime) and stime != "unscheduled" and _parse_iso(stime) is not None

    if is_sched:
        if ev:
            ev.start_time = stime
            ev.title = event_title_for_task(task_obj.id, getattr(task_obj, "title", ""), duration_min)
            ops.append({"op": "event_updated", "task_id": task_obj.id, "event_id": ev.id, "start_time": ev.start_time, "title": ev.title})
        else:
            ev = Event(
                title=event_title_for_task(task_obj.id, getattr(task_obj, "title", ""), duration_min),
                start_time=stime,
                created_at=datetime.utcnow(),
            )
            d.add(ev)
            d.flush()
            ops.append({"op": "event_created", "task_id": task_obj.id, "event_id": ev.id, "start_time": ev.start_time, "title": ev.title})
    else:
        if ev:
            ops.append({"op": "event_deleted", "task_id": task_obj.id, "event_id": ev.id, "title": ev.title})
            d.delete(ev)

    return ops


# Learning loop: Mood -> task success optimization

def best_task_titles_for_mood(mood: str, limit: int = 3) -> List[str]:
    d = db()
    try:
        rows = (
            d.query(Task.title, func.count(TaskFeedback.id).label("n"))
            .join(TaskFeedback, Task.id == TaskFeedback.task_id)
            .filter(TaskFeedback.mood == mood, TaskFeedback.completed == 1)
            .group_by(Task.title)
            .order_by(func.count(TaskFeedback.id).desc())
            .limit(limit)
            .all()
        )
        return [r[0] for r in rows if r and r[0]]
    finally:
        d.close()

def mood_tasktype_recommendations(mood: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Mood → task type optimization:
    Learns which TaskFeedback.task_type has highest success for a mood.
    """
    d = db()
    try:
        rows = (
            d.query(
                TaskFeedback.task_type.label("task_type"),
                func.avg(TaskFeedback.completed).label("success"),
                func.count(TaskFeedback.id).label("n"),
            )
            .filter(TaskFeedback.mood == mood)
            .group_by(TaskFeedback.task_type)
            .having(func.count(TaskFeedback.id) >= 2)
            .order_by(func.avg(TaskFeedback.completed).desc(), func.count(TaskFeedback.id).desc())
            .limit(limit)
            .all()
        )
        out = []
        for r in rows:
            out.append({"task_type": r.task_type or "general", "success": float(r.success or 0.0), "n": int(r.n or 0)})
        return out
    finally:
        d.close()

def reprioritize(task: Task, sent: dict):
    mood = (sent or {}).get("suggested_mood", "neutral")
    if mood in {"tired", "anxious", "overwhelmed"}:
        task.effective_priority = "low"
        if hasattr(task, "ai_priority_reason"):
            task.ai_priority_reason = "low energy mood"
    elif mood in {"focused", "motivated"}:
        task.effective_priority = "high"
        if hasattr(task, "ai_priority_reason"):
            task.ai_priority_reason = "focus window"
    else:
        task.effective_priority = task.user_priority
        if hasattr(task, "ai_priority_reason"):
            task.ai_priority_reason = None


# Core Endpoints

@app.post("/analyze")
async def analyze(payload: Dict[str, Any]):
    # keep existing behavior (graph expects payload["input"] typically)
    text = payload.get("input") or payload.get("text") or ""
    return await graph.run(text)


# Tasks

@app.get("/tasks")
def list_tasks(mode: Optional[str] = None):
    d = db()
    try:
        q = d.query(Task)
        if mode:
            q = q.filter(Task.mode == mode)
        return {"tasks": [task_to_dict(t) for t in q.order_by(Task.id.desc()).all()]}
    finally:
        d.close()

@app.post("/tasks")
def create_task(payload: TaskCreate):
    # preserve endpoint: manual create (no LLM)
    created = create_task_db(payload.description, payload.mode, payload.user_priority, payload.scheduled_time, duration_min=30)
    # mirror calendar ops into response (non-breaking, additive)
    ops = created.pop("_calendar_ops", [])
    return {"task": created, "calendar_ops": ops}

@app.patch("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    d = db()
    try:
        t = d.query(Task).filter(Task.id == task_id).first()
        if not t:
            raise HTTPException(404, "Task not found")

        # update fields
        if payload.description is not None:
            t.title = payload.description
        if payload.user_priority is not None:
            t.user_priority = payload.user_priority
            t.effective_priority = payload.user_priority
        if payload.scheduled_time is not None:
            t.scheduled_time = payload.scheduled_time
        if payload.status is not None and hasattr(t, "status"):
            t.status = payload.status

        # sync calendar (duration unknown on edit; keep 30m default)
        ops = sync_task_event_on_update(d, t, duration_min=30)

        d.commit()
        d.refresh(t)
        return {"task": task_to_dict(t), "calendar_ops": ops}
    finally:
        d.close()

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    d = db()
    try:
        t = d.query(Task).filter(Task.id == task_id).first()
        if not t:
            raise HTTPException(404, "Task not found")

        ops: List[Dict[str, Any]] = []
        ev = find_event_for_task(d, task_id)
        if ev:
            ops.append({"op": "event_deleted", "task_id": task_id, "event_id": ev.id, "title": ev.title})
            d.delete(ev)

        d.delete(t)
        d.commit()
        return {"status": "deleted", "calendar_ops": ops}
    finally:
        d.close()


# Schedule

@app.get("/schedule")
def list_events():
    d = db()
    try:
        return {"events": [event_to_dict(e) for e in d.query(Event).order_by(Event.id.desc()).all()]}
    finally:
        d.close()

@app.post("/schedule")
def create_event(payload: EventCreate):
    d = db()
    try:
        e = Event(title=payload.title, start_time=payload.start_time)
        # if model has created_at, let default handle, but safe:
        if hasattr(e, "created_at") and getattr(e, "created_at", None) is None:
            e.created_at = datetime.utcnow()
        d.add(e)
        d.commit()
        d.refresh(e)
        return event_to_dict(e)
    finally:
        d.close()

@app.delete("/schedule/{event_id}")
def delete_event(event_id: int):
    d = db()
    try:
        e = d.query(Event).filter(Event.id == event_id).first()
        if not e:
            raise HTTPException(404, "Event not found")
        d.delete(e)
        d.commit()
        return {"status": "deleted"}
    finally:
        d.close()


# Gamification (required by Streamlit)

@app.get("/gamification")
def gamification():
    d = db()
    try:
        stats = d.query(UserStats).first()
        if not stats:
            return {"current_streak": 0, "xp": 0, "level": 1}
        return {
            "current_streak": getattr(stats, "current_streak", 0) or 0,
            "xp": getattr(stats, "xp", 0) or 0,
            "level": getattr(stats, "level", 1) or 1,
        }
    finally:
        d.close()


# Feedback (required for Complete button + XP)

@app.post("/feedback")
def feedback(data: FeedbackIn):
    d = db()
    try:
        fb = TaskFeedback(
            task_id=data.task_id,
            mood=data.mood,
            mode=data.mode,
            task_type=data.task_type,
            completed=int(data.completed),
            timestamp=datetime.utcnow(),
        )

        # optional columns if present in your model:
        if hasattr(fb, "time_taken") and data.time_taken is not None:
            fb.time_taken = int(data.time_taken)
        if hasattr(fb, "time_of_day") and data.time_of_day is not None:
            fb.time_of_day = str(data.time_of_day)
        if hasattr(fb, "source"):
            fb.source = getattr(data, "source", "manual")

        d.add(fb)

        stats = d.query(UserStats).first()
        if not stats:
            stats = UserStats(current_streak=0, last_active_date=None, xp=0, level=1)
            d.add(stats)

        update_streak(stats.last_active_date, datetime.utcnow())
        xp_gained = calculate_xp(data.user_priority, data.completed, data.mood_boost)
        stats.xp = (stats.xp or 0) + xp_gained
        stats.level = get_level(stats.xp)

        # mark task status if supported
        t = d.query(Task).filter(Task.id == data.task_id).first()
        if t and hasattr(t, "status"):
            t.status = "done" if data.completed else "skipped"

        d.commit()

        return {
            "xp": stats.xp,
            "level": stats.level,
            "xp_gained": xp_gained,
            "streak": getattr(stats, "current_streak", 0) or 0,
        }
    finally:
        d.close()


# Analytics endpoints (required by UI)

@app.get("/analytics/mood")
def analytics_mood():
    return mood_productivity()

@app.get("/analytics/weekly")
def weekly_mood_success():
    d = db()
    try:
        rows = (
            d.query(
                TaskFeedback.mood.label("mood"),
                func.avg(TaskFeedback.completed).label("success"),
            )
            .filter(TaskFeedback.timestamp >= datetime.utcnow() - timedelta(days=7))
            .group_by(TaskFeedback.mood)
            .all()
        )
        return {r.mood: float(r.success or 0.0) for r in rows if r and r.mood}
    finally:
        d.close()


# Dashboard

@app.get("/dashboard")
def dashboard():
    d = db()
    try:
        tasks = d.query(Task).order_by(Task.id.desc()).limit(10).all()
        events = d.query(Event).order_by(Event.id.desc()).limit(10).all()
        stats = d.query(UserStats).first()
        return {
            "tasks": {"tasks": [task_to_dict(t) for t in tasks]},
            "schedule": {"events": [event_to_dict(e) for e in events]},
            "gamification": {
                "current_streak": stats.current_streak if stats else 0,
                "xp": stats.xp if stats else 0,
                "level": stats.level if stats else 1,
            },
            "analytics": {"mood": mood_productivity()},
        }
    finally:
        d.close()

# ==============================
# AI CHAT (ALL FEATURES KEPT + FIXED)
# - Intent classifier
# - Split compound sentences into multiple tasks
# - Confidence scoring to suppress auto-add when unsure
# - LLM returns staggered offsets -> we compute multiple slots
# - Event duration = duration_min (stored in event title)
# - Don’t schedule naps during meetings (buffer)
# - Auto-create calendar events for scheduled tasks
# - Chat response includes created vs rescheduled and calendar ops
# - Mood → task success learning + mood→task type optimization
# - Auto reprioritization preserved
# ==============================
@app.post("/ai/chat")
async def ai_chat(payload: ChatIn):
    text = (payload.text or "").strip()
    intent = detect_intent(text)

    # 1) Load schedule (events) for scheduling logic
    d0 = db()
    try:
        evs = d0.query(Event).order_by(Event.id.desc()).limit(80).all()
        events_payload = [{"id": e.id, "title": e.title, "start_time": e.start_time} for e in evs]
    finally:
        d0.close()

    calendar_ops: List[Dict[str, Any]] = []
    created_tasks: List[Dict[str, Any]] = []
    rescheduled_tasks: List[Dict[str, Any]] = []

    # 2) If explicit task intent -> create tasks (but still coach)
    if intent in {"ADD_TASK", "SCHEDULE"}:
        chunks = split_compound_tasks(text)

        # time anchor from full sentence (e.g., "in 2 hours")
        anchor = parse_natural_datetime(text)
        if anchor:
            try:
                anchor_dt = datetime.fromisoformat(anchor)
            except Exception:
                anchor_dt = None
        else:
            anchor_dt = None

        for i, raw_title in enumerate(chunks[:5]):
            title = clean_title(raw_title)
            conf = confidence_for_title(title)
            if conf < 0.55:
                # suppress very unsure explicit chunk (keeps your "confidence gating")
                continue

            avoid_naps = is_nap_task(title)

            # choose duration: naps shorter, otherwise 30 default
            duration_min = 10 if avoid_naps else 30

            sched_iso: Optional[str] = None
            changed = False

            if payload.auto_schedule:
                # try parse from chunk first
                parsed = parse_natural_datetime(title)
                # then anchor + stagger tasks if only one time is given
                if not parsed and anchor_dt:
                    # stagger by 15m per chunk
                    parsed = (anchor_dt + timedelta(minutes=15 * i)).replace(second=0, microsecond=0).isoformat()
                sched_iso, changed = ensure_no_conflict(parsed, events_payload, duration_min=duration_min, avoid_naps=avoid_naps)
            else:
                sched_iso = None

            created = create_task_db(
                desc=title,
                mode=payload.default_mode,
                pr=payload.default_priority,
                sched=sched_iso,
                duration_min=duration_min,
            )

            # pull calendar ops emitted by create_task_db
            ops = created.pop("_calendar_ops", [])
            calendar_ops.extend(ops)

            created["confidence"] = conf
            created_tasks.append(created)

            if changed and sched_iso:
                rescheduled_tasks.append({
                    "id": created["id"],
                    "description": created["description"],
                    "from": "parsed_or_anchor",
                    "to": sched_iso,
                })

            # keep events payload up to date so next task won't collide
            if sched_iso and sched_iso != "unscheduled":
                events_payload.append({"id": None, "title": event_title_for_task(created["id"], created["description"], duration_min), "start_time": sched_iso})

    # 3) Sentiment + auto reprioritization (kept)
    sent = analyze_sentiment(text) if text else {"label": "neutral", "suggested_mood": "neutral"}

    d1 = db()
    try:
        for t in d1.query(Task).all():
            reprioritize(t, sent)
        d1.commit()
    finally:
        d1.close()

    # 4) Learning signals to guide coaching/suggestions
    mood = (sent or {}).get("suggested_mood", "neutral")
    learned_titles = best_task_titles_for_mood(mood, limit=3)
    learned_types = mood_tasktype_recommendations(mood, limit=4)

    # 5) LLM coaching + suggestions (with confidence + duration + time offsets)
    prompt = f"""
You are MoodyBot: a calm productivity + wellbeing coach.

User message: "{text}"
Detected intent: {intent}
Sentiment: {sent}

Mood success learning:
- Past successful task titles for this mood: {learned_titles}
- Best task types for this mood (success rates): {learned_types}

Upcoming schedule events (start_time + title): {events_payload}

Return JSON ONLY in this exact format:
{{
  "reply": "1-3 short lines: validate + direction + a gentle plan",
  "suggestions": [
    {{
      "title": "actionable micro-task title (NOT generic like 'task')",
      "task_type": "prep|admin|deep_work|social|recovery|health|general",
      "reason": "why it helps now",
      "duration_min": 5,
      "auto_add": true,
      "confidence": 0.0,
      "time_offsets_min": [0, 30, 90, 180]
    }}
  ]
}}

Rules:
- NEVER output titles like "task", "todo", "something".
- Give 2-4 suggestions max.
- Confidence: 0.0-1.0 (higher when title is specific + helpful).
- If mood is tired/anxious/overwhelmed: include one recovery suggestion (but DO NOT schedule naps during meetings).
- Provide time_offsets_min so we can stagger into free slots.
"""
    data = llm_ask_json(prompt, retries=2)

    if not data:
        data = {
            "reply": "I hear you. Let’s make this lighter: one tiny step, then reassess.",
            "suggestions": [
                {
                    "title": "Write the next tiny step for your most urgent task",
                    "task_type": "prep",
                    "reason": "Reduces cognitive load and creates momentum",
                    "duration_min": 5,
                    "auto_add": True,
                    "confidence": 0.75,
                    "time_offsets_min": [0, 30, 90, 180],
                }
            ],
        }

    # 6) Auto-add suggestions (confidence gated) + auto-schedule with staggered slots
    auto_added: List[Dict[str, Any]] = []
    suppressed: List[Dict[str, Any]] = []

    suggestions = (data.get("suggestions") or [])[:6]

    for s in suggestions:
        title = clean_title(str(s.get("title", "") or ""))
        if not title or title.lower() in _BAD_TITLES:
            suppressed.append({"title": title or "(empty)", "reason": "bad_title", "confidence": 0.0})
            continue

        conf = float(s.get("confidence", confidence_for_title(title)))
        if not (payload.auto_add and bool(s.get("auto_add", True)) and conf >= 0.60):
            suppressed.append({"title": title, "reason": "low_conf_or_disabled", "confidence": conf})
            continue

        duration_min = int(s.get("duration_min", 10) or 10)
        duration_min = max(5, min(duration_min, 120))

        avoid_naps = is_nap_task(title)

        scheduled_time: Optional[str] = None
        changed = False
        candidate_slots: List[str] = []

        if payload.auto_schedule:
            # try natural time in title
            parsed = parse_natural_datetime(title)

            # if no explicit time, compute staggered free slots
            offsets = s.get("time_offsets_min") or [0, 30, 90, 180]
            try:
                offsets = [int(x) for x in offsets][:6]
            except Exception:
                offsets = [0, 30, 90, 180]

            base = datetime.now()

            candidate_slots = staggered_slots(
                events=events_payload,
                base=base if parsed is None else (_parse_iso(parsed) or base),
                offsets_min=offsets,
                duration_min=duration_min,
                avoid_naps=avoid_naps,
            )

            # pick the earliest candidate (or fix parsed if collides)
            if parsed:
                scheduled_time, changed = ensure_no_conflict(parsed, events_payload, duration_min=duration_min, avoid_naps=avoid_naps)
            else:
                scheduled_time = candidate_slots[0] if candidate_slots else find_next_available_slot(events_payload, duration_min=duration_min, avoid_naps=avoid_naps)
                changed = True
        else:
            scheduled_time = None

        created = create_task_db(
            desc=title,
            mode=payload.default_mode,
            pr=payload.default_priority,
            sched=scheduled_time,
            duration_min=duration_min,
        )

        ops = created.pop("_calendar_ops", [])
        calendar_ops.extend(ops)

        created["confidence"] = conf
        created["duration_min"] = duration_min
        if candidate_slots:
            created["candidate_slots"] = candidate_slots

        auto_added.append(created)

        # keep events payload updated to avoid collisions for next tasks
        if scheduled_time and scheduled_time != "unscheduled":
            events_payload.append({"id": None, "title": event_title_for_task(created["id"], created["description"], duration_min), "start_time": scheduled_time})

        if changed and scheduled_time:
            rescheduled_tasks.append({
                "id": created["id"],
                "description": created["description"],
                "from": "suggestion_time_or_none",
                "to": scheduled_time,
            })

    # 7) Response: show created vs rescheduled in chat window (additive fields)
    resp: Dict[str, Any] = {
        "type": "assistant_reply",
        "intent": intent,
        "sentiment": sent,
        "reply": str(data.get("reply", "") or ""),
        "suggestions": suggestions,
        "auto_added": auto_added,
        "suppressed": suppressed,
        "created_tasks": created_tasks,
        "rescheduled_tasks": rescheduled_tasks,
        "calendar_ops": calendar_ops,
        "mood_learning": {
            "mood": mood,
            "best_task_titles": learned_titles,
            "best_task_types": learned_types,
        },
    }

    # Backward compatibility with older UI code:
    if created_tasks:
        resp["created_task"] = created_tasks[0]
        resp["task"] = created_tasks[0]
    elif auto_added:
        # if only auto-added happened, still provide a task key
        resp["task"] = auto_added[0]

    return resp
