from flask import Blueprint


# ---------------------------------------
# Evidence Blueprint
# ---------------------------------------

evidence_bp = Blueprint(
    "evidence",
    __name__,
    template_folder="../templates"
)


# ---------------------------------------
# Import Routes
# ---------------------------------------

from . import routes