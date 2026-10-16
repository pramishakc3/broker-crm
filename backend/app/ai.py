"""AI client summary.

If ANTHROPIC_API_KEY is set, Claude summarises the client's file and suggests
next steps. Without a key (or if the API call fails) a rule-based fallback is
used, so the app always works offline and in tests.
"""
import json
import os
from datetime import date

from .models import Client, Stage

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

STAGE_NEXT_STEPS = {
    Stage.lead: ["Call the client to qualify their needs and borrowing goals",
                 "Send the fact-find form and document checklist"],
    Stage.contacted: ["Collect payslips, ID and bank statements",
                      "Run a serviceability check and shortlist suitable lenders"],
    Stage.application: ["Lodge the application and confirm receipt with the lender",
                        "Follow up the lender on any outstanding conditions"],
    Stage.approved: ["Send formal approval and loan documents to the client",
                     "Book the settlement date with all parties"],
    Stage.settled: ["Send a settlement thank-you and request a review",
                    "Schedule a 12-month rate review"],
    Stage.lost: ["Record the reason the deal was lost",
                 "Add the client to a 6-month nurture follow-up"],
}


def _client_context(client: Client) -> dict:
    return {
        "name": client.full_name,
        "loan_type": client.loan_type.value,
        "loan_amount": float(client.loan_amount or 0),
        "stage": client.stage.value,
        "lender": client.lender,
        "notes": [n.body for n in client.notes[:10]],
        "open_tasks": [
            {"title": t.title, "due": t.due_date.isoformat() if t.due_date else None}
            for t in client.tasks if not t.done
        ],
    }


def rule_based_summary(client: Client) -> dict:
    today = date.today()
    open_tasks = [t for t in client.tasks if not t.done]
    overdue = [t for t in open_tasks if t.due_date and t.due_date < today]
    amount = f"${float(client.loan_amount or 0):,.0f}"
    lender = f" with {client.lender}" if client.lender else ""
    summary = (
        f"{client.full_name} is at the '{client.stage.value}' stage for a "
        f"{client.loan_type.value.replace('_', ' ')} of {amount}{lender}. "
        f"{len(client.notes)} note(s) on file and {len(open_tasks)} open task(s)"
        + (f", {len(overdue)} overdue." if overdue else ".")
    )
    steps = [f"Overdue: {t.title}" for t in overdue] + STAGE_NEXT_STEPS[client.stage]
    return {"summary": summary, "next_steps": steps[:4], "source": "rules"}


def summarise_client(client: Client) -> dict:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return rule_based_summary(client)

    try:
        import anthropic

        prompt = (
            "You are an assistant for an Australian mortgage and leasing broker. "
            "Summarise this client file in 2 sentences and suggest up to 4 concrete "
            "next steps for the broker. Reply only with JSON of the form "
            '{"summary": "...", "next_steps": ["..."]}.\n\n'
            f"Client file:\n{json.dumps(_client_context(client), indent=2)}"
        )
        message = anthropic.Anthropic(api_key=api_key).messages.create(
            model=MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        start, end = text.find("{"), text.rfind("}")
        data = json.loads(text[start : end + 1])
        return {
            "summary": str(data["summary"]),
            "next_steps": [str(s) for s in data.get("next_steps", [])][:4],
            "source": "claude",
        }
    except Exception:
        # Never break the CRM because the AI service is unavailable
        return rule_based_summary(client)
