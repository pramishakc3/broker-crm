"""Load demo data: `python -m app.seed` (all names are fictional)."""
from datetime import date, timedelta

from .database import Base, SessionLocal, engine
from .models import Client, LoanType, Note, Stage, Task

DEMO = [
    ("Sarah Mitchell", "sarah.m@example.com", "0412 000 101", LoanType.home_loan, 650000, Stage.application, "Westpac"),
    ("James Nguyen", "j.nguyen@example.com", "0412 000 102", LoanType.refinance, 480000, Stage.contacted, None),
    ("Priya Sharma", "priya.s@example.com", "0412 000 103", LoanType.investment, 820000, Stage.approved, "ANZ"),
    ("Tom Walker", "tom.w@example.com", "0412 000 104", LoanType.car_lease, 55000, Stage.lead, None),
    ("Olivia Chen", "olivia.c@example.com", "0412 000 105", LoanType.equipment_finance, 120000, Stage.settled, "Macquarie"),
    ("Daniel Brooks", "d.brooks@example.com", "0412 000 106", LoanType.home_loan, 710000, Stage.lost, None),
]


def run():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.query(Client).count():
            print("Database already has data, skipping seed.")
            return
        today = date.today()
        for name, email, phone, loan_type, amount, stage, lender in DEMO:
            c = Client(full_name=name, email=email, phone=phone, loan_type=loan_type,
                       loan_amount=amount, stage=stage, lender=lender)
            c.notes.append(Note(body=f"Initial enquiry: {loan_type.value.replace('_', ' ')} around ${amount:,}."))
            c.tasks.append(Task(title="Follow-up call", due_date=today - timedelta(days=2)))
            c.tasks.append(Task(title="Send document checklist", due_date=today + timedelta(days=3)))
            db.add(c)
        db.commit()
        print(f"Seeded {len(DEMO)} demo clients.")


if __name__ == "__main__":
    run()
