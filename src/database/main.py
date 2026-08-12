#!/usr/bin/env python3.8

from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker

from .queries import (
    SensorQueries,
    SensorReadingQueries,
    WeatherReadingQueries,
)


"""Define the main class for database interaction."""


class DB(SensorQueries, SensorReadingQueries, WeatherReadingQueries):
    """Database base interface class.

    - Sets up the database engine and session manager.
    - Additional parent classes can be inherited to extend functionality.
    - Defines methods for common database operations.
    """

    def __init__(self, db_engine):
        # Set up the database session maker with the provided engine.
        self.engine = db_engine
        self.Session = sessionmaker(
            bind=self.engine,
            autoflush=True,
            autocommit=False,
            expire_on_commit=True
        )

    @contextmanager
    def session(self, current_session=None):
        """Context manager that can either pass thru an existing session or create a new one.

        Note: The goal of the pass-thru functionality is so we can define methods that can be
        called on their own or chained together in a single session. This way, if any part of
        the transaction fails, every chained commit gets rolled back and the current session
        is finally closed.

        Args:
            current_session: An existing SQLAlchemy session to use. If None, a new session is created.
        """

        s = current_session if current_session else self.Session()
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            # Only finalize the session if we created it here.
            if not current_session:
                s.close()

    # Define interface methods that reference multiple parent classes here.
