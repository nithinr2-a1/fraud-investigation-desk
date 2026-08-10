import os

from werkzeug.utils import secure_filename
from flask import send_from_directory

from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    current_app
)

from flask_login import (
    login_required,
    current_user
)

from bson import ObjectId

from .forms import EvidenceForm

from db import evidence
from db import cases

from . import evidence_bp
from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    current_app
)

from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from bson import ObjectId
import os

from . import evidence_bp
from .forms import EvidenceForm

from db import evidence, cases


# ---------------------------------------
# Evidence List
# ---------------------------------------
@evidence_bp.route("/evidence")
@login_required
def evidence_list():

    all_evidence = list(evidence.find())

    return render_template(
        "evidence.html",
        evidence=all_evidence
    )


# ---------------------------------------
# Upload Evidence
# ---------------------------------------
@evidence_bp.route("/evidence/add", methods=["GET", "POST"])
@login_required
def add_evidence():

    form = EvidenceForm()

    form.case_id.choices = [
        (str(c["_id"]), c["claim_id"])
        for c in cases.find()
    ]

    if form.validate_on_submit():

        uploaded_file = form.evidence_file.data

        filename = secure_filename(uploaded_file.filename)

        filepath = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            filename
        )

        uploaded_file.save(filepath)

        selected_case = cases.find_one({
            "_id": ObjectId(form.case_id.data)
        })

        evidence.insert_one({

            "case_id": form.case_id.data,

            "claim_id": selected_case["claim_id"],

            "filename": filename,

            "filepath": filepath,

            "evidence_type": form.evidence_type.data,

"description": form.description.data,

            "uploaded_by": current_user.username

        })

        flash("Evidence Uploaded Successfully", "success")

        return redirect(
            url_for("evidence.evidence_list")
        )

    return render_template(
        "add_evidence.html",
        form=form
    )
# ---------------------------------------
# Download Evidence
# ---------------------------------------
@evidence_bp.route("/evidence/download/<evidence_id>")
@login_required
def download_evidence(evidence_id):

    file = evidence.find_one(
        {"_id": ObjectId(evidence_id)}
    )

    if not file:
        flash("Evidence not found.", "danger")
        return redirect(url_for("evidence.evidence_list"))

    folder = current_app.config["UPLOAD_FOLDER"]

    return send_from_directory(
        folder,
        file["filename"],
        as_attachment=True
    )
# ---------------------------------------
# Delete Evidence
# ---------------------------------------
@evidence_bp.route("/evidence/delete/<evidence_id>")
@login_required
def delete_evidence(evidence_id):

    file = evidence.find_one(
        {"_id": ObjectId(evidence_id)}
    )

    if not file:
        flash("Evidence not found.", "danger")
        return redirect(url_for("evidence.evidence_list"))

    filepath = file["filepath"]

    if os.path.exists(filepath):
        os.remove(filepath)

    evidence.delete_one(
        {"_id": ObjectId(evidence_id)}
    )

    flash("Evidence Deleted Successfully", "success")

    return redirect(
        url_for("evidence.evidence_list")
    )