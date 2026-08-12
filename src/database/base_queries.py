#!/usr/bin/env python3.8

"""Base class for table-specific database actions.

This module provides common CRUD operations that can be inherited by table-specific action classes.
Each subclass should define a `model_class` attribute pointing to the SQLAlchemy model it operates on.
"""


class BaseTableQueries:
    """Base class providing common database operations for table action classes.

    Subclasses must define:
        model_class: The SQLAlchemy model class this action class operates on.
    """

    model_class = None  # To be overridden by subclasses

    def create(self, *args, current_session=None, **kwargs) -> dict:
        """Creates a new record in the database.

        Args:
            *args: Positional arguments to pass to the model constructor.
            current_session: Optional existing session to use.
            **kwargs: Keyword arguments to pass to the model constructor.

        Returns:
            Dictionary representation of the created record.
        """
        if self.model_class is None:
            raise NotImplementedError("Subclass must define model_class attribute")

        with self.session(current_session) as s:
            new_record = self.model_class(*args, **kwargs)
            s.add(new_record)
            return new_record.get_dict()

    def _get_by_id(self, record_id: int, current_session):
        """Returns the model instance matching the given primary-key ID.

        Private method - assumes session is already being managed.

        Args:
            record_id: The primary-key ID to search for.
            current_session: An active SQLAlchemy session.

        Returns:
            Model instance matching the primary-key ID.

        Raises:
            ValueError: If no record with the given ID is found.
        """
        if self.model_class is None:
            raise NotImplementedError("Subclass must define model_class attribute")

        record = current_session.get(self.model_class, record_id)
        if not record:
            model_name = self.model_class.__name__
            raise ValueError(f"{model_name} with id '{record_id}' not found.")

        return record

    def get_by_id(self, record_id: int, current_session=None) -> dict:
        """Returns record data matching the given primary-key ID.

        Args:
            record_id: The primary-key ID to search for.
            current_session: Optional existing session to use.

        Returns:
            Dictionary representation of the record.
        """
        if self.model_class is None:
            raise NotImplementedError("Subclass must define model_class attribute")

        with self.session(current_session) as s:
            record = self._get_by_id(record_id, s)
            return record.get_dict()

    def update_by_id(self, record_id: int, settings_dict: dict, current_session=None) -> dict:
        """Updates fields for the record with the given primary-key ID.

        Args:
            record_id: The primary-key ID of the record to update.
            settings_dict: Dictionary of field names and values to update.
            current_session: Optional existing session to use.

        Returns:
            Dictionary representation of the updated record.

        Raises:
            ValueError: If a field in settings_dict doesn't exist on the model.
        """
        if self.model_class is None:
            raise NotImplementedError("Subclass must define model_class attribute")

        with self.session(current_session) as s:
            record = self._get_by_id(record_id, s)

            for key, value in settings_dict.items():
                if not hasattr(record, key):
                    model_name = self.model_class.__name__
                    raise ValueError(f"{model_name} has no attribute '{key}' to update.")
                setattr(record, key, value)

            return record.get_dict()

    def delete_by_id(self, record_id: int, current_session=None) -> dict:
        """Deletes the record with the given primary-key ID.

        Args:
            record_id: The primary-key ID of the record to delete.
            current_session: Optional existing session to use.

        Returns:
            Dictionary representation of the deleted record.

        Raises:
            ValueError: If no record with the given ID is found.
        """
        if self.model_class is None:
            raise NotImplementedError("Subclass must define model_class attribute")

        with self.session(current_session) as s:
            record = self._get_by_id(record_id, s)
            record_dict = record.get_dict()
            s.delete(record)
        return record_dict
