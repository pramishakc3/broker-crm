from datetime import date, datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LoanType(str, Enum):
    home_loan = "home_loan"
    refinance = "refinance"
    investment = "investment"
    car_lease = "car_lease"
    equipment_finance = "equipment_finance"
    personal_loan = "personal_loan"


class Stage(str, Enum):
    lead = "lead"
    contacted = "contacted"
    application = "application"
    approved = "approved"
    settled = "settled"
    lost = "lost"


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), index=True)
    email: Mapped[str | None] = mapped_column(String(160), index=True)
    phone: Mapped[str | None] = mapped_column(String(40))
    loan_type: Mapped[LoanType] = mapped_column(SAEnum(LoanType, native_enum=False))
    loan_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    stage: Mapped[Stage] = mapped_column(SAEnum(Stage, native_enum=False), default=Stage.lead, index=True)
    lender: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    notes: Mapped[list["Note"]] = relationship(
        back_populates="client", cascade="all, delete-orphan", order_by="Note.created_at.desc()"
    )
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="client", cascade="all, delete-orphan", order_by="Task.due_date"
    )


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    client: Mapped[Client] = relationship(back_populates="notes")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    due_date: Mapped[date | None] = mapped_column(Date)
    done: Mapped[bool] = mapped_column(Boolean, default=False)

    client: Mapped[Client] = relationship(back_populates="tasks")
