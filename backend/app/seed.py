
from backend.app.db import SessionLocal
from backend.app.models import Requester, Ticket

db = SessionLocal()

try:
    # Create sample employees
    employee1 = Requester(
        employee_id="EMP001",
        name="Rahul Sharma",
        email="rahul@example.com",
        department="Engineering"
    )

    employee2 = Requester(
        employee_id="EMP002",
        name="Priya Das",
        email="priya@example.com",
        department="Finance"
    )

    db.add_all([employee1, employee2])
    db.commit()

    # Create sample tickets
    ticket1 = Ticket(
        requester_id=employee1.id,
        title="Laptop not starting",
        description="My laptop is not powering on.",
        category="Hardware",
        priority="High",
        status="New"
    )

    ticket2 = Ticket(
        requester_id=employee2.id,
        title="Unable to access email",
        description="I cannot log in to my company email.",
        category="Access",
        priority="Medium",
        status="New"
    )

    db.add_all([ticket1, ticket2])
    db.commit()

    print("Sample employees and tickets inserted successfully!")

except Exception as e:
    db.rollback()
    print("Error:", e)

finally:
    db.close()
