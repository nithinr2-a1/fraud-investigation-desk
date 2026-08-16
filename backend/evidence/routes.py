import os
import uuid

from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId

from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    current_app,
    send_from_directory
)

from flask_login import (
    login_required,
    current_user
)

from werkzeug.utils import secure_filename

from . import evidence_bp
from .forms import EvidenceForm

from db import evidence
from db import cases


# ============================================================
# Evidence List
# ============================================================

@evidence_bp.route("/evidence")
@login_required
def evidence_list():

    # --------------------------------------------------------
    # Get latest evidence first
    # --------------------------------------------------------

    all_evidence = list(
        evidence.find().sort(
            "uploaded_date",
            -1
        )
    )

    # --------------------------------------------------------
    # Display Evidence
    # --------------------------------------------------------

    return render_template(
        "evidence.html",
        evidence=all_evidence
    )


# ============================================================
# Upload Evidence
# ============================================================

@evidence_bp.route(
    "/evidence/add",
    methods=["GET", "POST"]
)
@login_required
def add_evidence():

    form = EvidenceForm()

    # --------------------------------------------------------
    # Populate Case dropdown
    #
    # Only retrieve fields required by the dropdown.
    # --------------------------------------------------------

    form.case_id.choices = [
        (
            str(case["_id"]),
            case.get(
                "claim_id",
                str(case["_id"])
            )
        )
        for case in cases.find(
            {},
            {
                "_id": 1,
                "claim_id": 1
            }
        )
    ]

    # --------------------------------------------------------
    # Process Upload
    # --------------------------------------------------------

    if form.validate_on_submit():

        uploaded_file = form.evidence_file.data

        # ----------------------------------------------------
        # Validate uploaded file
        # ----------------------------------------------------

        if not uploaded_file:

            flash(
                "Please select an evidence file.",
                "danger"
            )

            return render_template(
                "add_evidence.html",
                form=form
            )

        # ----------------------------------------------------
        # Secure original filename
        # ----------------------------------------------------

        original_filename = secure_filename(
            uploaded_file.filename
        )

        if not original_filename:

            flash(
                "Invalid filename.",
                "danger"
            )

            return render_template(
                "add_evidence.html",
                form=form
            )

        # ----------------------------------------------------
        # Validate selected Case
        # ----------------------------------------------------

        try:

            selected_case = cases.find_one(
                {
                    "_id": ObjectId(
                        form.case_id.data
                    )
                }
            )

        except (InvalidId, TypeError):

            selected_case = None

        if not selected_case:

            flash(
                "Selected case was not found.",
                "danger"
            )

            return render_template(
                "add_evidence.html",
                form=form
            )

        # ----------------------------------------------------
        # Upload folder
        # ----------------------------------------------------

        upload_folder = current_app.config[
            "UPLOAD_FOLDER"
        ]

        os.makedirs(
            upload_folder,
            exist_ok=True
        )

        # ----------------------------------------------------
        # Generate unique server filename
        #
        # This prevents files with the same name from
        # overwriting each other.
        # ----------------------------------------------------

        unique_filename = (
            uuid.uuid4().hex
            + "_"
            + original_filename
        )

        filepath = os.path.join(
            upload_folder,
            unique_filename
        )

        # ----------------------------------------------------
        # Save physical file
        # ----------------------------------------------------

        try:

            uploaded_file.save(
                filepath
            )

        except OSError:

            flash(
                "Unable to save the evidence file.",
                "danger"
            )

            return render_template(
                "add_evidence.html",
                form=form
            )

        # ----------------------------------------------------
        # Create Evidence document
        # ----------------------------------------------------

        evidence_document = {

            # Case relationship
            "case_id":
                form.case_id.data,

            # Claim relationship
            "claim_id":
                selected_case.get(
                    "claim_id",
                    form.case_id.data
                ),

            # Original filename shown to users
            "filename":
                original_filename,

            # Unique physical filename
            "stored_filename":
                unique_filename,

            # Physical path
            "filepath":
                filepath,

            # Evidence category
            "evidence_type":
                form.evidence_type.data,

            # Description
            "description":
                form.description.data,

            # Uploaded user
            "uploaded_by":
                current_user.username,

            # Upload timestamp
            "uploaded_date":
                datetime.utcnow()
        }

        # ----------------------------------------------------
        # Save metadata to MongoDB
        # ----------------------------------------------------

        try:

            evidence.insert_one(
                evidence_document
            )

        except Exception:

            # ------------------------------------------------
            # If MongoDB save fails, remove the physical file
            # to avoid leaving an orphan file.
            # ------------------------------------------------

            if os.path.exists(filepath):

                try:

                    os.remove(filepath)

                except OSError:

                    pass

            flash(
                "Evidence could not be saved. Please try again.",
                "danger"
            )

            return render_template(
                "add_evidence.html",
                form=form
            )

        # ----------------------------------------------------
        # Success
        # ----------------------------------------------------

        flash(
            "Evidence Uploaded Successfully",
            "success"
        )

        return redirect(
            url_for(
                "evidence.evidence_list"
            )
        )

    # --------------------------------------------------------
    # Display Upload Page
    # --------------------------------------------------------

    return render_template(
        "add_evidence.html",
        form=form
    )


# ============================================================
# Download Evidence
# ============================================================

@evidence_bp.route(
    "/evidence/download/<evidence_id>"
)
@login_required
def download_evidence(evidence_id):

    # --------------------------------------------------------
    # Validate Evidence ID
    # --------------------------------------------------------

    try:

        evidence_object_id = ObjectId(
            evidence_id
        )

    except (InvalidId, TypeError):

        flash(
            "Invalid evidence ID.",
            "danger"
        )

        return redirect(
            url_for(
                "evidence.evidence_list"
            )
        )

    # --------------------------------------------------------
    # Find Evidence
    # --------------------------------------------------------

    file = evidence.find_one(
        {
            "_id": evidence_object_id
        }
    )

    if not file:

        flash(
            "Evidence not found.",
            "danger"
        )

        return redirect(
            url_for(
                "evidence.evidence_list"
            )
        )

    # --------------------------------------------------------
    # Get Upload Folder
    # --------------------------------------------------------

    folder = current_app.config[
        "UPLOAD_FOLDER"
    ]

    # --------------------------------------------------------
    # Get stored filename
    #
    # New records use stored_filename.
    #
    # Old records fall back to filename for compatibility.
    # --------------------------------------------------------

    stored_filename = file.get(
        "stored_filename"
    )

    if not stored_filename:

        stored_filename = file.get(
            "filename"
        )

    if not stored_filename:

        flash(
            "Evidence file information is missing.",
            "danger"
        )

        return redirect(
            url_for(
                "evidence.evidence_list"
            )
        )

    # --------------------------------------------------------
    # Check physical file
    # --------------------------------------------------------

    filepath = os.path.join(
        folder,
        stored_filename
    )

    if not os.path.exists(filepath):

        flash(
            "Evidence file is missing from the server.",
            "danger"
        )

        return redirect(
            url_for(
                "evidence.evidence_list"
            )
        )

    # --------------------------------------------------------
    # Download
    #
    # The user receives the original filename.
    # --------------------------------------------------------

    return send_from_directory(
        folder,
        stored_filename,
        as_attachment=True,
        download_name=file.get(
            "filename",
            stored_filename
        )
    )


# ============================================================
# Delete Evidence
# ============================================================

@evidence_bp.route(
    "/evidence/delete/<evidence_id>"
)
@login_required
def delete_evidence(evidence_id):

    # --------------------------------------------------------
    # Validate Evidence ID
    # --------------------------------------------------------

    try:

        evidence_object_id = ObjectId(
            evidence_id
        )

    except (InvalidId, TypeError):

        flash(
            "Invalid evidence ID.",
            "danger"
        )

        return redirect(
            url_for(
                "evidence.evidence_list"
            )
        )

    # --------------------------------------------------------
    # Find Evidence
    # --------------------------------------------------------

    file = evidence.find_one(
        {
            "_id": evidence_object_id
        }
    )

    if not file:

        flash(
            "Evidence not found.",
            "danger"
        )

        return redirect(
            url_for(
                "evidence.evidence_list"
            )
        )

    # --------------------------------------------------------
    # Determine physical filename
    # --------------------------------------------------------

    stored_filename = file.get(
        "stored_filename"
    )

    if not stored_filename:

        stored_filename = file.get(
            "filename"
        )

    # --------------------------------------------------------
    # Delete physical file
    # --------------------------------------------------------

    if stored_filename:

        upload_folder = current_app.config[
            "UPLOAD_FOLDER"
        ]

        filepath = os.path.join(
            upload_folder,
            stored_filename
        )

        if os.path.exists(filepath):

            try:

                os.remove(filepath)

            except OSError:

                flash(
                    "Evidence record found, but the physical file could not be deleted.",
                    "warning"
                )

    # --------------------------------------------------------
    # Delete MongoDB record
    # --------------------------------------------------------

    evidence.delete_one(
        {
            "_id": evidence_object_id
        }
    )

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    flash(
        "Evidence Deleted Successfully",
        "success"
    )

    return redirect(
        url_for(
            "evidence.evidence_list"
        )
    )