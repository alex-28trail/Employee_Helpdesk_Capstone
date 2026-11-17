
from backend.app.db import engine, Base

# Import all models so SQLAlchemy registers them
from backend.app.models import (
    Requester,
    Ticket,
    TicketActivity,
    AISuggestion,
    AIFeedback
)

def create_tables():
    Base.metadata.create_all(bind=engine)
    print("All database tables created successfully!")


if __name__ == "__main__":
    create_tables()
