"""Climate logger web application."""

from flask import Flask

from src.database import db as db


app = Flask(__name__)


from . import routes as routes

__all__ = ["app", "db", "routes"]
