from flask import render_template, redirect, url_for, flash
from flask_login import login_required

from . import claims_bp
from .forms import ClaimForm
from db import claims
from bson import ObjectId
from flask import abort


# ---------------------------------------
# List Claims
# ---------------------------------------
@claims_bp.route("/claims")
@login_required
def claims_list():

    all_claims = list(claims.find())

    return render_template(
        "claims.html",
        claims=all_claims
    )


# ---------------------------------------
# Add Claim
# ---------------------------------------
@claims_bp.route("/claims/add", methods=["GET", "POST"])
@login_required
def add_claim():

    form = ClaimForm()

    if form.validate_on_submit():

        document = {

            "claim_id": form.claim_id.data,
            "claim_type": form.claim_type.data,
            "claim_amount": form.claim_amount.data,
            "policy_limit": form.policy_limit.data,
            "premium": form.premium.data,
            "policy_age_days": form.policy_age_days.data,
            "prior_claims": form.prior_claims.data,
            "report_delay_days": form.report_delay_days.data,
            "customer_age": form.customer_age.data,

            "status": "New"
        }

        claims.insert_one(document)

        flash("Claim Added Successfully", "success")

        return redirect(url_for("claims.claims_list"))

    return render_template(
        "add_claim.html",
        form=form
    )
# ---------------------------------------
# View Claim
# ---------------------------------------
@claims_bp.route("/claims/view/<claim_id>")
@login_required
def view_claim(claim_id):

    claim = claims.find_one({"_id": ObjectId(claim_id)})

    if not claim:
        abort(404)

    return render_template(
        "view_claim.html",
        claim=claim
    )
# ---------------------------------------
# Edit Claim
# ---------------------------------------
@claims_bp.route("/claims/edit/<claim_id>", methods=["GET", "POST"])
@login_required
def edit_claim(claim_id):

    claim = claims.find_one({"_id": ObjectId(claim_id)})

    if claim is None:
        abort(404)

    form = ClaimForm(data=claim)

    if form.validate_on_submit():

        claims.update_one(
            {"_id": ObjectId(claim_id)},
            {
                "$set": {
                    "claim_id": form.claim_id.data,
                    "claim_type": form.claim_type.data,
                    "claim_amount": form.claim_amount.data,
                    "policy_limit": form.policy_limit.data,
                    "premium": form.premium.data,
                    "policy_age_days": form.policy_age_days.data,
                    "prior_claims": form.prior_claims.data,
                    "report_delay_days": form.report_delay_days.data,
                    "customer_age": form.customer_age.data,
                }
            }
        )

        flash("Claim updated successfully.", "success")

        return redirect(url_for("claims.view_claim", claim_id=claim_id))

    return render_template(
        "edit_claim.html",
        form=form,
        claim=claim
    )
# ---------------------------------------
# Delete Claim
# ---------------------------------------
@claims_bp.route("/claims/delete/<claim_id>")
@login_required
def delete_claim(claim_id):

    claims.delete_one(
        {"_id": ObjectId(claim_id)}
    )

    flash(
        "Claim Deleted Successfully",
        "success"
    )

    return redirect(
        url_for("claims.claims_list")
    )