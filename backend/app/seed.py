"""Seed demo data (F2.2).  Run from backend/ after init_db:

    python -m app.seed

Safe to re-run: it does nothing if requesters already exist.
"""
from datetime import datetime, timedelta, timezone

from app.db import SessionLocal
from app.models import AIFeedback, AISuggestion, Requester, Ticket, TicketActivity

REQUESTERS = [
    ("EMP001", "Rahul Sharma", "rahul.sharma@example.com", "Engineering"),
    ("EMP002", "Priya Das", "priya.das@example.com", "Finance"),
    ("EMP003", "Asha Kumar", "asha.kumar@example.com", "Human Resources"),
    ("EMP004", "Vikram Nair", "vikram.nair@example.com", "Sales"),
    ("EMP005", "Meera Iyer", "meera.iyer@example.com", "Marketing"),
    ("EMP006", "Arjun Menon", "arjun.menon@example.com", "Operations"),
]

# (requester index, title, description, category, priority, status, days ago)
TICKETS = [
    (0, "Laptop not starting", "My laptop does not power on even when plugged in. The charging light stays off.",
     "Hardware", "High", "New", 0),
    (1, "Unable to access email", "I cannot log in to Outlook since this morning. It says my password is incorrect.",
     "Access", "Medium", "In Progress", 1),
    (2, "Wireless keyboard not typing", "My wireless keyboard stopped responding today. The laptop keyboard still works.",
     "Hardware", "Low", "New", 0),
    (1, "Finance shared drive unreachable", "Nobody in Finance can open the S: drive since 9am. Month-end close is blocked.",
     "Network", "High", "In Progress", 0),
    (3, "VPN disconnects every few minutes", "When working from home the VPN drops roughly every 5 minutes.",
     "Network", "Medium", "New", 2),
    (4, "Request Adobe Photoshop licence", "I need Photoshop installed for the new campaign artwork.",
     "Software", "Low", "Resolved", 6),
    (5, "Excel crashes when opening large files", "Excel closes without an error when I open the monthly ops report.",
     "Software", "Medium", "Resolved", 4),
    (3, "Printer on 2nd floor jamming", "The HP printer near the pantry jams on every second page.",
     "Hardware", "Low", "In Progress", 3),
    (0, "Need access to Jira project", "Please give me access to the PAYMENTS project in Jira for the new sprint.",
     "Access", "Medium", "New", 1),
    (4, "Monitor flickering", "My external monitor flickers every few seconds after the latest Windows update.",
     "Other", "Low", "New", 0),
]


def seed() -> None:
    db = SessionLocal()
    try:
        if db.query(Requester).count():
            print("Seed skipped: data already present.")
            return

        people = [Requester(employee_id=e, name=n, email=m, department=d) for e, n, m, d in REQUESTERS]
        db.add_all(people)
        db.flush()

        now = datetime.now(timezone.utc)
        tickets = []
        for idx, title, desc, cat, pri, status, days in TICKETS:
            created = now - timedelta(days=days, hours=2)
            t = Ticket(requester_id=people[idx].id, title=title, description=desc,
                       category=cat, priority=pri, status=status, created_at=created, updated_at=created)
            db.add(t)
            db.flush()
            tickets.append(t)

            db.add(TicketActivity(ticket_id=t.id, performed_by=people[idx].name, activity_type="created",
                                  description="Ticket created", new_status="New", created_at=created))
            if status in ("In Progress", "Resolved"):
                db.add(TicketActivity(ticket_id=t.id, performed_by="Support Staff", activity_type="status_change",
                                      description="Status moved to In Progress", old_status="New",
                                      new_status="In Progress", created_at=created + timedelta(minutes=30)))
                db.add(TicketActivity(ticket_id=t.id, performed_by="Support Staff", activity_type="comment",
                                      description="Looking into this now.", created_at=created + timedelta(minutes=35)))
            if status == "Resolved":
                db.add(TicketActivity(ticket_id=t.id, performed_by="Support Staff", activity_type="status_change",
                                      description="Status moved to Resolved", old_status="In Progress",
                                      new_status="Resolved", created_at=created + timedelta(hours=3)))

        # A couple of AI suggestions, one already reviewed by staff.
        s1 = AISuggestion(
            ticket_id=tickets[3].id, suggested_category="Network", suggested_priority="High",
            priority_reason="A whole department is blocked from a business-critical file share.",
            troubleshooting_steps=["Check the file server is online", "Verify DNS resolves the share name",
                                   "Review recent network or permission changes"],
            model_name="qwen2.5:3b", prompt_version="v1", latency_ms=4200,
        )
        s2 = AISuggestion(
            ticket_id=tickets[1].id, suggested_category="Access", suggested_priority="Low",
            priority_reason="Single user affected; webmail may work as a workaround.",
            troubleshooting_steps=["Confirm the account is not locked", "Reset the password via self-service",
                                   "Clear cached Outlook credentials"],
            model_name="qwen2.5:3b", prompt_version="v1", latency_ms=3900,
        )
        db.add_all([s1, s2])
        db.flush()
        db.add(AIFeedback(suggestion_id=s2.id, ticket_id=tickets[1].id, decision="corrected", useful=True,
                          final_category="Access", final_priority="Medium",
                          comment="User is fully blocked from email, so Medium."))
        db.add(TicketActivity(ticket_id=tickets[1].id, performed_by="Support Staff", activity_type="ai_feedback",
                              description="AI suggestion corrected by support: priority Low -> Medium. Marked useful."))

        db.commit()
        print(f"Seeded {len(people)} requesters and {len(tickets)} tickets.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
