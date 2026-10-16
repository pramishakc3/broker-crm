import os
from datetime import date, timedelta

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_crm.db")
os.environ.pop("ANTHROPIC_API_KEY", None)

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def make_client(client, **overrides):
    payload = {
        "full_name": "Sarah Mitchell",
        "email": "sarah@example.com",
        "phone": "0412 000 101",
        "loan_type": "home_loan",
        "loan_amount": 650000,
        "stage": "lead",
    }
    payload.update(overrides)
    res = client.post("/api/clients", json=payload)
    assert res.status_code == 201, res.text
    return res.json()


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_create_and_get_client(client):
    created = make_client(client)
    res = client.get(f"/api/clients/{created['id']}")
    assert res.status_code == 200
    body = res.json()
    assert body["full_name"] == "Sarah Mitchell"
    assert body["notes"] == [] and body["tasks"] == []


def test_validation_rejects_bad_input(client):
    res = client.post("/api/clients", json={"full_name": "", "loan_type": "home_loan", "loan_amount": -5})
    assert res.status_code == 422


def test_search_and_filter(client):
    make_client(client, full_name="Sarah Mitchell", stage="lead")
    make_client(client, full_name="James Nguyen", email="james@example.com", stage="approved", loan_type="refinance")
    assert [c["full_name"] for c in client.get("/api/clients", params={"q": "james"}).json()] == ["James Nguyen"]
    assert len(client.get("/api/clients", params={"stage": "lead"}).json()) == 1
    assert len(client.get("/api/clients", params={"loan_type": "refinance"}).json()) == 1


def test_update_stage(client):
    c = make_client(client)
    res = client.patch(f"/api/clients/{c['id']}", json={"stage": "application", "lender": "Westpac"})
    assert res.status_code == 200
    assert res.json()["stage"] == "application"
    assert res.json()["lender"] == "Westpac"


def test_notes_and_tasks(client):
    c = make_client(client)
    assert client.post(f"/api/clients/{c['id']}/notes", json={"body": "Called client"}).status_code == 201
    task = client.post(f"/api/clients/{c['id']}/tasks", json={"title": "Get payslips"}).json()
    done = client.patch(f"/api/tasks/{task['id']}", json={"done": True}).json()
    assert done["done"] is True
    detail = client.get(f"/api/clients/{c['id']}").json()
    assert len(detail["notes"]) == 1 and len(detail["tasks"]) == 1


def test_dashboard_totals(client):
    a = make_client(client, stage="application", loan_amount=500000)
    make_client(client, full_name="Olivia Chen", email="o@example.com", stage="settled", loan_amount=100000)
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    client.post(f"/api/clients/{a['id']}/tasks", json={"title": "Overdue call", "due_date": yesterday})
    d = client.get("/api/dashboard").json()
    assert d["total_clients"] == 2
    assert d["active_pipeline_amount"] == 500000
    assert d["settled_amount"] == 100000
    assert d["open_tasks"] == 1 and d["overdue_tasks"] == 1


def test_ai_summary_falls_back_to_rules_without_api_key(client):
    c = make_client(client, stage="application")
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    client.post(f"/api/clients/{c['id']}/tasks", json={"title": "Chase lender", "due_date": yesterday})
    res = client.post(f"/api/clients/{c['id']}/ai-summary").json()
    assert res["source"] == "rules"
    assert "application" in res["summary"]
    assert res["next_steps"][0] == "Overdue: Chase lender"


def test_delete_client(client):
    c = make_client(client)
    assert client.delete(f"/api/clients/{c['id']}").status_code == 204
    assert client.get(f"/api/clients/{c['id']}").status_code == 404
