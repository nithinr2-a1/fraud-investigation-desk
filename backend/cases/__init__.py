from flask import Blueprint

cases_bp = Blueprint(
    "cases",
    __name__,
    template_folder="../templates"
)

from . import routes