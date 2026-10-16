from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .models import LoanType, Stage


class NoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class NoteOut(NoteCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    due_date: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    due_date: date | None = None
    done: bool | None = None


class TaskOut(TaskCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    client_id: int
    done: bool


class ClientBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    loan_type: LoanType
    loan_amount: float = Field(ge=0)
    stage: Stage = Stage.lead
    lender: str | None = Field(default=None, max_length=80)


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    loan_type: LoanType | None = None
    loan_amount: float | None = Field(default=None, ge=0)
    stage: Stage | None = None
    lender: str | None = Field(default=None, max_length=80)


class ClientOut(ClientBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class ClientDetail(ClientOut):
    notes: list[NoteOut] = []
    tasks: list[TaskOut] = []


class StageCount(BaseModel):
    stage: Stage
    count: int
    total_amount: float


class Dashboard(BaseModel):
    total_clients: int
    active_pipeline_amount: float
    settled_amount: float
    open_tasks: int
    overdue_tasks: int
    by_stage: list[StageCount]


class AISummary(BaseModel):
    summary: str
    next_steps: list[str]
    source: str  # "claude" or "rules"
