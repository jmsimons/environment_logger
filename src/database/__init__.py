from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base


"""Initialize the database resources."""


# Load database config.
db_filename = "climate.db"

# Define database resources.
Base = declarative_base()
db_engine = create_engine(f"sqlite:///{db_filename}")

# Import models to register them with Base.
from . import models as models


def initialize_database() -> None:
    """Create any database tables that do not already exist."""
    Base.metadata.create_all(bind=db_engine)


# Initialize the database.
from .main import DB
db = DB(db_engine)


__all__ = ["db", "db_filename", "initialize_database", "models"]
