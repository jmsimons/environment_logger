"""Climate logger web application."""

from flask import Flask


app = Flask(__name__)


from . import main as main

__all__ = ["app", "main"]
