from flask import render_template, redirect, url_for, flash, abort
from flask_login import login_required
from bson import ObjectId
from datetime import datetime

from . import cases_bp
from .forms import CaseForm

from db import cases
from db import claims


# ---------------------------------------
# List Cases
# ---------------------------------------
@cases_bp.route("/cases")
@login_required
def cases_list():

    all_cases = list(cases.find())

    return render_template(
        "cases.html",
        cases=all_cases
    )


# ---------------------------------------
# Add Case
# ---------------------------------------
@cases_bp.route("/cases/add", methods=["GET", "POST"])
@login_required
def add_case():

    form = CaseForm()

    # Populate Claim dropdown
    form.claim_id.choices = [
        (str(c["_id"]), c["claim_id"])
        for c in claims.find()
    ]

    if form.validate_on_submit():

        selected_claim = claims.find_one(
            {"_id": ObjectId(form.claim_id.data)}
        )

        document = {
            "claim_object_id": form.claim_id.data,
            "claim_id": selected_claim["claim_id"],
            "investigator": form.investigator.data,
            "priority": form.priority.data,
            "status": form.status.data,
            "remarks": form.remarks.data,
            "opened_date": datetime.utcnow()
        }

        cases.insert_one(document)

        flash("Case Created Successfully", "success")

        return redirect(url_for("cases.cases_list"))

    return render_template(
        "add_case.html",
        form=form
    )
# ---------------------------------------
# View Case
# ---------------------------------------
@cases_bp.route("/cases/view/<case_id>")
@login_required
def view_case(case_id):

    case = cases.find_one(
        {"_id": ObjectId(case_id)}
    )

    if not case:
        abort(404)

    return render_template(
        "view_case.html",
        case=case
    )
# ---------------------------------------
# Edit Case
# ---------------------------------------
@cases_bp.route("/cases/edit/<case_id>", methods=["GET", "POST"])
@login_required
def edit_case(case_id):

    case = cases.find_one(
        {"_id": ObjectId(case_id)}
    )

    if not case:
        abort(404)

    form = CaseForm(data=case)

    form.claim_id.choices = [
        (str(c["_id"]), c["claim_id"])
        for c in claims.find()
    ]

    if form.validate_on_submit():

        selected_claim = claims.find_one(
            {"_id": ObjectId(form.claim_id.data)}
        )

        cases.update_one(
            {"_id": ObjectId(case_id)},
            {
                "$set": {
                    "claim_object_id": form.claim_id.data,
                    "claim_id": selected_claim["claim_id"],
                    "investigator": form.investigator.data,
                    "priority": form.priority.data,
                    "status": form.status.data,
                    "remarks": form.remarks.data
                }
            }
        )

        flash("Case Updated Successfully", "success")

        return redirect(url_for("cases.cases_list"))

    return render_template(
        "add_case.html",
        form=form
    )
# ---------------------------------------
# Delete Case
# ---------------------------------------
@cases_bp.route("/cases/delete/<case_id>")
@login_required
def delete_case(case_id):

    cases.delete_one(
        {"_id": ObjectId(case_id)}
    )

    flash("Case Deleted Successfully", "success")

    return redirect(url_for("cases.cases_list"))