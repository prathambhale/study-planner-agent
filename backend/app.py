from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlmodel import Field, SQLModel, create_engine, Session, select
import math
import uuid
import os

DATABASE_URL = "sqlite:///plans.db"
engine = create_engine(DATABASE_URL, echo=False)

app = FastAPI(title="Personal Study Planner Agent")

# --- Database models ---
class Plan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_uuid: str
    user_id: str
    created_at: datetime
    start_date: date
    end_date: date
    hours_per_day: float
    session_length_minutes: int

class Subject(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_uuid: str
    name: str
    weight: int
    topics_count: Optional[int] = None

class SessionItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_uuid: str
    session_uuid: str
    date: date
    subject: str
    topic: Optional[str]
    minutes: int
    status: str

# --- Pydantic models ---
class SubjectIn(BaseModel):
    name: str
    weight: int = 3
    topics_count: Optional[int] = None

class CreatePlanIn(BaseModel):
    user_id: str
    subjects: List[SubjectIn]
    start_date: date
    end_date: Optional[date] = None
    hours_per_day: float = 3.0
    session_length_minutes: int = 50

# --- DB init ---
def init_db():
    if not os.path.exists("plans.db"):
        SQLModel.metadata.create_all(engine)

init_db()

# --- Scheduler ---
def schedule_sessions(plan_uuid: str, start: date, end: date, hours_per_day: float, session_length_minutes: int, subjects: List[SubjectIn]):
    days = (end - start).days + 1
    buffer_days = max(1, min(3, days // 14))
    active_days = max(1, days - buffer_days)

    points = []
    for s in subjects:
        tcount = s.topics_count or 10
        p = s.weight * tcount
        points.append((s.name, p))

    total_points = sum(p for _, p in points)
    factor = 0.2
    total_sessions = max(1, math.ceil(total_points * factor))

    sessions_per_day_capacity = max(1, int((hours_per_day * 60) // session_length_minutes))
    max_possible = sessions_per_day_capacity * active_days

    if total_sessions > max_possible:
        total_sessions = max_possible

    subject_sessions = {}
    for name, p in points:
        share = p / total_points if total_points > 0 else 1 / len(points)
        subject_sessions[name] = max(1, int(round(share * total_sessions)))

    ssum = sum(subject_sessions.values())
    while ssum < total_sessions:
        mx = max(points, key=lambda x: x[1])[0]
        subject_sessions[mx] += 1
        ssum += 1

    while ssum > total_sessions:
        candidates = [k for k, v in subject_sessions.items() if v > 1]
        if not candidates:
            break
        mn = min(candidates, key=lambda x: subject_sessions[x])
        subject_sessions[mn] -= 1
        ssum -= 1

    sessions = []
    day_count = 0
    remaining = subject_sessions.copy()
    subject_order = list(remaining.keys())

    while day_count < active_days:
        daily_slots = sessions_per_day_capacity
        j = 0
        while daily_slots > 0 and sum(remaining.values()) > 0:
            sub = subject_order[j % len(subject_order)]
            if remaining[sub] > 0:
                sessions.append({
                    "session_uuid": str(uuid.uuid4()),
                    "date": (start + timedelta(days=day_count)).isoformat(),
                    "subject": sub,
                    "topic": None,
                    "minutes": session_length_minutes,
                    "status": "pending"
                })
                remaining[sub] -= 1
                daily_slots -= 1
            j += 1
        day_count += 1

    return sessions

# --- Endpoints ---
@app.post("/create-plan")
def create_plan(payload: CreatePlanIn):
    if payload.end_date is None:
        end = payload.start_date + timedelta(days=14)
    else:
        end = payload.end_date

    if end < payload.start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")

    plan_uuid = str(uuid.uuid4())

    with Session(engine) as session:
        plan = Plan(
            plan_uuid=plan_uuid,
            user_id=payload.user_id,
            created_at=datetime.utcnow(),
            start_date=payload.start_date,
            end_date=end,
            hours_per_day=payload.hours_per_day,
            session_length_minutes=payload.session_length_minutes,
        )
        session.add(plan)
        session.commit()

        for s in payload.subjects:
            subj = Subject(
                plan_uuid=plan_uuid,
                name=s.name,
                weight=s.weight,
                topics_count=s.topics_count
            )
            session.add(subj)

        session.commit()

        sessions_list = schedule_sessions(
            plan_uuid,
            payload.start_date,
            end,
            payload.hours_per_day,
            payload.session_length_minutes,
            payload.subjects
        )

        for item in sessions_list:
            si = SessionItem(
                plan_uuid=plan_uuid,
                session_uuid=item["session_uuid"],
                date=datetime.fromisoformat(item["date"]).date(),
                subject=item["subject"],
                topic=item["topic"],
                minutes=item["minutes"],
                status=item["status"]
            )
            session.add(si)

        session.commit()

    return {
        "plan_id": plan_uuid,
        "days": (end - payload.start_date).days + 1,
        "sessions_created": len(sessions_list)
    }


@app.get("/get-plan")
def get_plan(plan_id: str):
    with Session(engine) as session:
        plan = session.exec(select(Plan).where(Plan.plan_uuid == plan_id)).first()
        if not plan:
            raise HTTPException(status_code=404, detail="plan not found")

        subs = session.exec(select(Subject).where(Subject.plan_uuid == plan_id)).all()
        items = session.exec(
            select(SessionItem).where(SessionItem.plan_uuid == plan_id).order_by(SessionItem.date)
        ).all()

        return {"plan": plan, "subjects": subs, "sessions": items}


@app.post("/update-progress")
def update_progress(plan_id: str, session_uuid: str, status: str):
    if status not in ("done", "skipped"):
        raise HTTPException(status_code=400, detail="invalid status")

    with Session(engine) as session:
        item = session.exec(
            select(SessionItem)
            .where(SessionItem.plan_uuid == plan_id, SessionItem.session_uuid == session_uuid)
        ).first()

        if not item:
            raise HTTPException(status_code=404, detail="session not found")

        item.status = status
        session.add(item)
        session.commit()

        return {"updated": True, "session": item}


@app.get("/export")
def export_plan(plan_id: str):
    with Session(engine) as session:
        items = session.exec(
            select(SessionItem).where(SessionItem.plan_uuid == plan_id).order_by(SessionItem.date)
        ).all()

        export = [
            {
                "date": str(i.date),
                "subject": i.subject,
                "minutes": i.minutes,
                "status": i.status,
                "session_uuid": i.session_uuid
            }
            for i in items
        ]
        return {"export": export}
