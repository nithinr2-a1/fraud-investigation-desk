from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    abort,
    request
)

from flask_login import login_required

from bson import ObjectId
from datetime import datetime

from . import cases_bp
from .forms import CaseForm

from db import cases
from db import claims
from db import predictions
from db import evidence


# =========================================================
# List Cases
# =========================================================

@cases_bp.route("/cases")
@login_required
def cases_list():

    # -----------------------------------------------------
    # Get all cases
    # Latest cases first
    # -----------------------------------------------------

    all_cases = list(
        cases.find().sort(
            "opened_date",
            -1
        )
    )

    # -----------------------------------------------------
    # Calculate summary statistics
    # -----------------------------------------------------

    total_cases = len(all_cases)

    open_cases = cases.count_documents({
        "status": "Open"
    })

    closed_cases = cases.count_documents({
        "status": "Closed"
    })

    high_priority_cases = cases.count_documents({
        "priority": "High"
    })

    # -----------------------------------------------------
    # Display Cases
    # -----------------------------------------------------

    return render_template(
        "cases.html",
        cases=all_cases,
        total_cases=total_cases,
        open_cases=open_cases,
        closed_cases=closed_cases,
        high_priority_cases=high_priority_cases
    )


# =========================================================
# Add Case
# =========================================================

@cases_bp.route(
    "/cases/add",
    methods=["GET", "POST"]
)
@login_required
def add_case():

    form = CaseForm()

    # -----------------------------------------------------
    # Populate Claim dropdown
    # Only retrieve fields required by dropdown
    # -----------------------------------------------------

    form.claim_id.choices = [
        (
            str(claim["_id"]),
            claim.get(
                "claim_id",
                str(claim["_id"])
            )
        )
        for claim in claims.find(
            {},
            {
                "_id": 1,
                "claim_id": 1
            }
        )
    ]

    # -----------------------------------------------------
    # Pre-select claim when coming from
    # Fraud Prediction
    #
    # Example:
    # /cases/add?claim_id=66a...
    # -----------------------------------------------------

    claim_id_from_prediction = request.args.get(
        "claim_id"
    )

    if (
        claim_id_from_prediction
        and request.method == "GET"
    ):

        try:

            selected_claim = claims.find_one(
                {
                    "_id": ObjectId(
                        claim_id_from_prediction
                    )
                }
            )

            if selected_claim:

                form.claim_id.data = (
                    claim_id_from_prediction
                )

        except Exception:

            flash(
                "Invalid claim selected.",
                "danger"
            )

    # -----------------------------------------------------
    # Create Case
    # -----------------------------------------------------

    if form.validate_on_submit():

        # -------------------------------------------------
        # Get selected claim
        # -------------------------------------------------

        try:

            selected_claim = claims.find_one(
                {
                    "_id": ObjectId(
                        form.claim_id.data
                    )
                }
            )

        except Exception:

            selected_claim = None

        # -------------------------------------------------
        # Validate selected claim
        # -------------------------------------------------

        if not selected_claim:

            flash(
                "Selected claim was not found.",
                "danger"
            )

            return redirect(
                url_for(
                    "cases.add_case"
                )
            )

        # -------------------------------------------------
        # Get latest ML prediction
        # for selected claim
        # -------------------------------------------------

        latest_prediction = predictions.find_one(
            {
                "claim_object_id":
                    form.claim_id.data
            },
            sort=[
                (
                    "prediction_date",
                    -1
                )
            ]
        )

        # -------------------------------------------------
        # Create Case document
        # -------------------------------------------------

        document = {

            "claim_object_id":
                form.claim_id.data,

            "claim_id":
                selected_claim.get(
                    "claim_id",
                    form.claim_id.data
                ),

            "investigator":
                form.investigator.data,

            "priority":
                form.priority.data,

            "status":
                form.status.data,

            "remarks":
                form.remarks.data,

            "opened_date":
                datetime.utcnow()
        }

        # -------------------------------------------------
        # Attach latest ML prediction
        # -------------------------------------------------

        if latest_prediction:

            document["prediction_id"] = str(
                latest_prediction["_id"]
            )

            document["risk_score"] = (
                latest_prediction.get(
                    "risk_score",
                    0
                )
            )

            document["risk_percentage"] = (
                latest_prediction.get(
                    "risk_percentage",
                    0
                )
            )

            document["risk_level"] = (
                latest_prediction.get(
                    "risk_level",
                    "Unknown"
                )
            )

            document["anomaly_score"] = (
                latest_prediction.get(
                    "anomaly_score",
                    0
                )
            )

            document["prediction_date"] = (
                latest_prediction.get(
                    "prediction_date"
                )
            )

        # -------------------------------------------------
        # Save Case
        # -------------------------------------------------

        cases.insert_one(
            document
        )

        flash(
            "Case Created Successfully",
            "success"
        )

        return redirect(
            url_for(
                "cases.cases_list"
            )
        )

    # -----------------------------------------------------
    # Display Add Case page
    # -----------------------------------------------------

    return render_template(
        "add_case.html",
        form=form
    )


# =========================================================
# View Case
# =========================================================

@cases_bp.route(
    "/cases/view/<case_id>"
)
@login_required
def view_case(case_id):

    # -----------------------------------------------------
    # Validate ObjectId
    # -----------------------------------------------------

    try:

        object_id = ObjectId(
            case_id
        )

    except Exception:

        abort(404)

    # -----------------------------------------------------
    # Get Case
    # -----------------------------------------------------

    case = cases.find_one(
        {
            "_id": object_id
        }
    )

    if not case:

        abort(404)

    # -----------------------------------------------------
    # Get Evidence for this Case
    # -----------------------------------------------------

    case_evidence = list(
        evidence.find(
            {
                "case_id": case_id
            }
        ).sort(
            "uploaded_date",
            -1
        )
    )

    # -----------------------------------------------------
    # Display Case Details
    # -----------------------------------------------------

    return render_template(
        "view_case.html",
        case=case,
        evidence=case_evidence
    )


# =========================================================
# Edit Case
# =========================================================

@cases_bp.route(
    "/cases/edit/<case_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_case(case_id):

    # -----------------------------------------------------
    # Validate ObjectId
    # -----------------------------------------------------

    try:

        object_id = ObjectId(
            case_id
        )

    except Exception:

        abort(404)

    # -----------------------------------------------------
    # Get existing case
    # -----------------------------------------------------

    case = cases.find_one(
        {
            "_id": object_id
        }
    )

    if not case:

        abort(404)

    # -----------------------------------------------------
    # Populate form with existing data
    # -----------------------------------------------------

    form = CaseForm(
        data=case
    )

    # -----------------------------------------------------
    # Populate Claim dropdown
    # -----------------------------------------------------

    form.claim_id.choices = [
        (
            str(claim["_id"]),
            claim.get(
                "claim_id",
                str(claim["_id"])
            )
        )
        for claim in claims.find(
            {},
            {
                "_id": 1,
                "claim_id": 1
            }
        )
    ]

    # -----------------------------------------------------
    # Update Case
    # -----------------------------------------------------

    if form.validate_on_submit():

        # -------------------------------------------------
        # Get selected claim
        # -------------------------------------------------

        try:

            selected_claim = claims.find_one(
                {
                    "_id": ObjectId(
                        form.claim_id.data
                    )
                }
            )

        except Exception:

            selected_claim = None

        # -------------------------------------------------
        # Validate selected claim
        # -------------------------------------------------

        if not selected_claim:

            flash(
                "Selected claim was not found.",
                "danger"
            )

            return redirect(
                url_for(
                    "cases.edit_case",
                    case_id=case_id
                )
            )

        # -------------------------------------------------
        # Update Case
        #
        # ML prediction is intentionally NOT
        # recalculated here.
        # -------------------------------------------------

        cases.update_one(
            {
                "_id": object_id
            },
            {
                "$set": {

                    "claim_object_id":
                        form.claim_id.data,

                    "claim_id":
                        selected_claim.get(
                            "claim_id",
                            form.claim_id.data
                        ),

                    "investigator":
                        form.investigator.data,

                    "priority":
                        form.priority.data,

                    "status":
                        form.status.data,

                    "remarks":
                        form.remarks.data
                }
            }
        )

        flash(
            "Case Updated Successfully",
            "success"
        )

        return redirect(
            url_for(
                "cases.view_case",
                case_id=case_id
            )
        )

    # -----------------------------------------------------
    # Display Edit Case page
    # -----------------------------------------------------

    return render_template(
        "edit_case.html",
        form=form,
        case=case
    )


# =========================================================
# Delete Case
# =========================================================

@cases_bp.route(
    "/cases/delete/<case_id>"
)
@login_required
def delete_case(case_id):

    # -----------------------------------------------------
    # Validate ObjectId
    # -----------------------------------------------------

    try:

        object_id = ObjectId(
            case_id
        )

    except Exception:

        abort(404)

    # -----------------------------------------------------
    # Delete Case
    # -----------------------------------------------------

    result = cases.delete_one(
        {
            "_id": object_id
        }
    )

    if result.deleted_count == 0:

        abort(404)

    # -----------------------------------------------------
    # Delete Evidence associated with Case
    #
    # Evidence uses the string case_id.
    # -----------------------------------------------------

    evidence.delete_many(
        {
            "case_id": case_id
        }
    )

    # -----------------------------------------------------
    # Success message
    # -----------------------------------------------------

    flash(
        "Case Deleted Successfully",
        "success"
    )

    # -----------------------------------------------------
    # Return to Cases
    # -----------------------------------------------------

    return redirect(
        url_for(
            "cases.cases_list"
        )
    )