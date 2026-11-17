"""Create all tables from the ORM models.  Run from backend/:

    python -m app.init_db            # create missing tables
    python -m app.init_db --reset    # DROP everything and recreate (dev only)
"""
import sys

import app.models  # noqa: F401  (registers every model on Base.metadata)
from app.db import Base, engine


def create_tables(reset: bool = False) -> None:
    if reset:
        Base.metadata.drop_all(bind=engine)
        print("Dropped all tables.")
    Base.metadata.create_all(bind=engine)
    print("All database tables created successfully!")


if __name__ == "__main__":
    create_tables(reset="--reset" in sys.argv)
