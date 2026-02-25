from datetime import datetime, timezone
from sqlalchemy.orm import declarative_base


def utc_now():
    """Return current UTC time (timezone-aware). Use for SQLAlchemy Column default/onupdate."""
    return datetime.now(timezone.utc)


Base = declarative_base()

