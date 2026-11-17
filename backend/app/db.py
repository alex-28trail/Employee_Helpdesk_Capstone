from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# Uses settings.database_url (DATABASE_URL, or built from DB_* values), so tests can
# point the app at a separate *_test database. echo is off: SQL parameters would
# otherwise put ticket descriptions into the logs (F1.4).
engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
