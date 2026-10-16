import os
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from . import models, schemas
from .ai import summarise_client
from .database import Base, engine, get_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Broker CRM API",
    description="A lightweight CRM for mortgage and leasing brokers, with AI client summaries.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_client(db: Session, client_id: int) -> models.Client:
    client = db.scalar(
        select(models.Client)
        .options(selectinload(models.Client.notes), selectinload(models.Client.tasks))
        .where(models.Client.id == client_id)
    )
    if not client:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Client not found")
    return client


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------- Clients ----------

@app.get("/api/clients", response_model=list[schemas.ClientOut])
def list_clients(
    q: str | None = Query(default=None, description="Search name, email or phone"),
    stage: models.Stage | None = None,
    loan_type: models.LoanType | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(models.Client).order_by(models.Client.updated_at.desc())
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(models.Client.full_name).like(like),
                func.lower(models.Client.email).like(like),
                models.Client.phone.like(f"%{q}%"),
            )
        )
    if stage:
        stmt = stmt.where(models.Client.stage == stage)
    if loan_type:
        stmt = stmt.where(models.Client.loan_type == loan_type)
    return db.scalars(stmt).all()


@app.post("/api/clients", response_model=schemas.ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(payload: schemas.ClientCreate, db: Session = Depends(get_db)):
    client = models.Client(**payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@app.get("/api/clients/{client_id}", response_model=schemas.ClientDetail)
def get_client(client_id: int, db: Session = Depends(get_db)):
    return _get_client(db, client_id)


@app.patch("/api/clients/{client_id}", response_model=schemas.ClientOut)
def update_client(client_id: int, payload: schemas.ClientUpdate, db: Session = Depends(get_db)):
    client = _get_client(db, client_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


@app.delete("/api/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    db.delete(_get_client(db, client_id))
    db.commit()


# ---------- Notes ----------

@app.post("/api/clients/{client_id}/notes", response_model=schemas.NoteOut, status_code=201)
def add_note(client_id: int, payload: schemas.NoteCreate, db: Session = Depends(get_db)):
    client = _get_client(db, client_id)
    note = models.Note(client_id=client.id, body=payload.body)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


# ---------- Tasks ----------

@app.post("/api/clients/{client_id}/tasks", response_model=schemas.TaskOut, status_code=201)
def add_task(client_id: int, payload: schemas.TaskCreate, db: Session = Depends(get_db)):
    client = _get_client(db, client_id)
    task = models.Task(client_id=client.id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@app.patch("/api/tasks/{task_id}", response_model=schemas.TaskOut)
def update_task(task_id: int, payload: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


# ---------- Dashboard & AI ----------

@app.get("/api/dashboard", response_model=schemas.Dashboard)
def dashboard(db: Session = Depends(get_db)):
    rows = db.execute(
        select(models.Client.stage, func.count(), func.coalesce(func.sum(models.Client.loan_amount), 0))
        .group_by(models.Client.stage)
    ).all()
    counts = {stage: (count, float(total)) for stage, count, total in rows}
    by_stage = [
        schemas.StageCount(stage=s, count=counts.get(s, (0, 0.0))[0], total_amount=counts.get(s, (0, 0.0))[1])
        for s in models.Stage
    ]
    active = {models.Stage.lead, models.Stage.contacted, models.Stage.application, models.Stage.approved}
    open_tasks = db.scalar(select(func.count()).select_from(models.Task).where(models.Task.done.is_(False)))
    overdue = db.scalar(
        select(func.count()).select_from(models.Task)
        .where(models.Task.done.is_(False), models.Task.due_date < date.today())
    )
    return schemas.Dashboard(
        total_clients=sum(c.count for c in by_stage),
        active_pipeline_amount=sum(c.total_amount for c in by_stage if c.stage in active),
        settled_amount=counts.get(models.Stage.settled, (0, 0.0))[1],
        open_tasks=open_tasks or 0,
        overdue_tasks=overdue or 0,
        by_stage=by_stage,
    )


@app.post("/api/clients/{client_id}/ai-summary", response_model=schemas.AISummary)
def ai_summary(client_id: int, db: Session = Depends(get_db)):
    return summarise_client(_get_client(db, client_id))
