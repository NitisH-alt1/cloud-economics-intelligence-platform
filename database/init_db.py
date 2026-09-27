from database.db import Base, engine

# Import models so SQLAlchemy registers every table.
from database.models import (
    User,
    Organization,
    Membership,
    Project,
)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("DATABASE TABLES: CREATED")
