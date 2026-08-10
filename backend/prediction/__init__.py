from flask import Blueprint

prediction_bp = Blueprint(
    "prediction",
    __name__,
    template_folder="../templates"
)

from . import routes