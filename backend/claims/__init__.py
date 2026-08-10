from flask import Blueprint

claims_bp = Blueprint(
    "claims",
    __name__,
    template_folder="../templates"
)

from . import routes