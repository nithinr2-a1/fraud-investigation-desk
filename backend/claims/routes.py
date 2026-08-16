from datetime import datetime
import math
import re

from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request
)

from flask_login import login_required

from bson import ObjectId

from . import claims_bp
from .forms import ClaimForm

from db import claims, predictions


# =========================================================
# Helper Functions
# =========================================================

def get_object_id(value):
    """
    Safely convert a value to MongoDB ObjectId.
    Returns None if conversion is not possible.
    """

    try:
        return ObjectId(value)
    except Exception:
        return None


# =========================================================
# CLAIM LIST
# =========================================================

@claims_bp.route("/claims")
@login_required
def claims_list():

    # -----------------------------------------------------
    # Pagination
    # -----------------------------------------------------

    try:
        page = int(request.args.get("page", 1))
    except (TypeError, ValueError):
        page = 1

    if page < 1:
        page = 1

    per_page = 10

    # -----------------------------------------------------
    # Filters
    # -----------------------------------------------------

    search = request.args.get(
        "search",
        ""
    ).strip()

    selected_claim_type = request.args.get(
        "claim_type",
        ""
    ).strip()

    selected_status = request.args.get(
        "status",
        ""
    ).strip()

    selected_risk = request.args.get(
        "risk",
        ""
    ).strip()

    # -----------------------------------------------------
    # Get available claim types
    # -----------------------------------------------------

    claim_types = sorted(
        [
            value
            for value in claims.distinct("claim_type")
            if value
        ]
    )

    # -----------------------------------------------------
    # Base MongoDB query
    # -----------------------------------------------------

    query_conditions = []

    # -----------------------------------------------------
    # Search by Claim ID
    # -----------------------------------------------------

    if search:

        query_conditions.append({
            "claim_id": {
                "$regex": re.escape(search),
                "$options": "i"
            }
        })

    # -----------------------------------------------------
    # Claim Type
    # -----------------------------------------------------

    if selected_claim_type:

        query_conditions.append({
            "claim_type": selected_claim_type
        })

    # -----------------------------------------------------
    # Status
    # -----------------------------------------------------

    if selected_status:

        query_conditions.append({
            "$or": [
                {
                    "status": selected_status
                },
                {
                    "display_status": selected_status
                }
            ]
        })

    # =====================================================
    # ML RISK FILTER
    # =====================================================

    risk_object_ids = []
    risk_claim_ids = []

    predicted_object_ids = []
    predicted_claim_ids = []

    # -----------------------------------------------------
    # Read all predictions
    #
    # Latest predictions are sorted first.
    # -----------------------------------------------------

    all_prediction_records = list(
        predictions.find(
            {},
            {
                "claim_object_id": 1,
                "claim_id": 1,
                "risk_level": 1,
                "risk_percentage": 1,
                "prediction_date": 1
            }
        ).sort(
            "prediction_date",
            -1
        )
    )

    # -----------------------------------------------------
    # Build latest prediction mapping
    # -----------------------------------------------------

    risk_map = {}

    for prediction in all_prediction_records:

        risk_level = prediction.get(
            "risk_level",
            "Not Predicted"
        )

        risk_percentage = prediction.get(
            "risk_percentage",
            0
        )

        risk_data = {
            "risk_level": risk_level,
            "risk_percentage": risk_percentage
        }

        # -------------------------------------------------
        # ObjectId mapping
        # -------------------------------------------------

        claim_object_id = prediction.get(
            "claim_object_id"
        )

        if claim_object_id:

            claim_object_id_string = str(
                claim_object_id
            )

            # Keep only the latest prediction
            if claim_object_id_string not in risk_map:

                risk_map[
                    claim_object_id_string
                ] = risk_data

        # -------------------------------------------------
        # Claim ID mapping
        # -------------------------------------------------

        claim_id = prediction.get(
            "claim_id"
        )

        if claim_id:

            claim_key = f"CLAIM:{claim_id}"

            # Keep only latest prediction
            if claim_key not in risk_map:

                risk_map[claim_key] = risk_data

    # -----------------------------------------------------
    # Build predicted claim lists
    # -----------------------------------------------------

    for prediction in all_prediction_records:

        claim_object_id = prediction.get(
            "claim_object_id"
        )

        if claim_object_id:

            object_id = get_object_id(
                claim_object_id
            )

            if object_id:

                if object_id not in predicted_object_ids:

                    predicted_object_ids.append(
                        object_id
                    )

        claim_id = prediction.get(
            "claim_id"
        )

        if claim_id:

            if claim_id not in predicted_claim_ids:

                predicted_claim_ids.append(
                    claim_id
                )

    # -----------------------------------------------------
    # Apply selected ML risk
    # -----------------------------------------------------

    if selected_risk:

        # =================================================
        # High / Medium / Low
        # =================================================

        if selected_risk in [
            "High",
            "Medium",
            "Low"
        ]:

            for prediction in all_prediction_records:

                if prediction.get(
                    "risk_level"
                ) != selected_risk:

                    continue

                claim_object_id = prediction.get(
                    "claim_object_id"
                )

                if claim_object_id:

                    object_id = get_object_id(
                        claim_object_id
                    )

                    if object_id:

                        if object_id not in risk_object_ids:

                            risk_object_ids.append(
                                object_id
                            )

                claim_id = prediction.get(
                    "claim_id"
                )

                if claim_id:

                    if claim_id not in risk_claim_ids:

                        risk_claim_ids.append(
                            claim_id
                        )

            # -----------------------------------------
            # No matching predictions
            # -----------------------------------------

            if not risk_object_ids and not risk_claim_ids:

                query_conditions.append({
                    "_id": {
                        "$in": []
                    }
                })

            else:

                risk_conditions = []

                if risk_object_ids:

                    risk_conditions.append({
                        "_id": {
                            "$in": risk_object_ids
                        }
                    })

                if risk_claim_ids:

                    risk_conditions.append({
                        "claim_id": {
                            "$in": risk_claim_ids
                        }
                    })

                query_conditions.append({
                    "$or": risk_conditions
                })

        # =================================================
        # NOT PREDICTED
        # =================================================

        elif selected_risk == "Not Predicted":

            not_predicted_conditions = []

            if predicted_object_ids:

                not_predicted_conditions.append({
                    "_id": {
                        "$nin": predicted_object_ids
                    }
                })

            if predicted_claim_ids:

                not_predicted_conditions.append({
                    "claim_id": {
                        "$nin": predicted_claim_ids
                    }
                })

            if not_predicted_conditions:

                query_conditions.append({
                    "$and": not_predicted_conditions
                })

    # =====================================================
    # Build final MongoDB query
    # =====================================================

    if query_conditions:

        if len(query_conditions) == 1:

            mongo_query = query_conditions[0]

        else:

            mongo_query = {
                "$and": query_conditions
            }

    else:

        mongo_query = {}

    # =====================================================
    # Count filtered records
    # =====================================================

    filtered_count = claims.count_documents(
        mongo_query
    )

    # -----------------------------------------------------
    # Total pages
    # -----------------------------------------------------

    total_pages = max(
        1,
        math.ceil(
            filtered_count / per_page
        )
    )

    # -----------------------------------------------------
    # Keep page inside valid range
    # -----------------------------------------------------

    if page > total_pages:

        page = total_pages

    skip = (
        page - 1
    ) * per_page

    # =====================================================
    # Fetch claims
    # =====================================================

    claim_records = list(
        claims.find(
            mongo_query
        )
        .sort(
            "created_at",
            -1
        )
        .skip(skip)
        .limit(per_page)
    )

    # =====================================================
    # Attach display information
    # =====================================================

    for claim in claim_records:

        claim_object_id = str(
            claim["_id"]
        )

        claim_id = claim.get(
            "claim_id"
        )

        # -------------------------------------------------
        # Status
        # -------------------------------------------------

        display_status = claim.get(
            "status",
            "New"
        )

        claim[
            "display_status"
        ] = display_status

        # -------------------------------------------------
        # Try prediction by ObjectId
        # -------------------------------------------------

        prediction = risk_map.get(
            claim_object_id
        )

        # -------------------------------------------------
        # If not found, try Claim ID
        # -------------------------------------------------

        if not prediction and claim_id:

            prediction = risk_map.get(
                f"CLAIM:{claim_id}"
            )

        # -------------------------------------------------
        # ML risk information
        # -------------------------------------------------

        if prediction:

            claim[
                "display_risk_level"
            ] = prediction.get(
                "risk_level",
                "Not Predicted"
            )

            claim[
                "display_risk_percentage"
            ] = prediction.get(
                "risk_percentage",
                0
            )

        else:

            claim[
                "display_risk_level"
            ] = "Not Predicted"

            claim[
                "display_risk_percentage"
            ] = None

        # -------------------------------------------------
        # Created date
        # -------------------------------------------------

        claim[
            "display_created_at"
        ] = claim.get(
            "created_at"
        )

    # =====================================================
    # Summary statistics
    # =====================================================

    total_claims = claims.count_documents({})

    under_review = claims.count_documents({
        "$or": [
            {
                "status": "Under Review"
            },
            {
                "display_status": "Under Review"
            }
        ]
    })

    # -----------------------------------------------------
    # High risk count
    # -----------------------------------------------------

    high_risk = predictions.count_documents({
        "risk_level": "High"
    })

    # =====================================================
    # Render Claims Page
    # =====================================================

    return render_template(
        "claims.html",

        # Claims
        claims=claim_records,

        # Summary
        total_claims=total_claims,
        under_review=under_review,
        high_risk=high_risk,

        # Filtering
        search=search,
        claim_types=claim_types,

        selected_claim_type=selected_claim_type,
        selected_status=selected_status,
        selected_risk=selected_risk,

        # Results
        filtered_count=filtered_count,

        # Pagination
        page=page,
        total_pages=total_pages
    )


# =========================================================
# ADD CLAIM
# =========================================================

@claims_bp.route(
    "/claims/add",
    methods=["GET", "POST"]
)
@login_required
def add_claim():

    form = ClaimForm()

    if form.validate_on_submit():

        # -------------------------------------------------
        # Check duplicate Claim ID
        # -------------------------------------------------

        existing_claim = claims.find_one({
            "claim_id": form.claim_id.data.strip()
        })

        if existing_claim:

            flash(
                "A claim with this Claim ID already exists.",
                "danger"
            )

            return render_template(
                "add_claim.html",
                form=form
            )

        # -------------------------------------------------
        # Create claim document
        # -------------------------------------------------

        claim_document = {

            "claim_id":
                form.claim_id.data.strip(),

            "claim_type":
                form.claim_type.data.strip(),

            "claim_amount":
                form.claim_amount.data,

            "policy_limit":
                form.policy_limit.data,

            "premium":
                form.premium.data,

            "policy_age_days":
                form.policy_age_days.data,

            "prior_claims":
                form.prior_claims.data,

            "report_delay_days":
                form.report_delay_days.data,

            "customer_age":
                form.customer_age.data,

            "police_report":
                bool(
                    form.police_report.data
                ),

            "status":
                "New",

            "created_at":
                datetime.utcnow(),

            "updated_at":
                datetime.utcnow()
        }

        # -------------------------------------------------
        # Save claim
        # -------------------------------------------------

        claims.insert_one(
            claim_document
        )

        flash(
            "Claim added successfully.",
            "success"
        )

        return redirect(
            url_for(
                "claims.claims_list"
            )
        )

    return render_template(
        "add_claim.html",
        form=form
    )


# =========================================================
# VIEW CLAIM
# =========================================================

@claims_bp.route(
    "/claims/view/<claim_id>"
)
@login_required
def view_claim(claim_id):

    object_id = get_object_id(
        claim_id
    )

    if not object_id:

        flash(
            "Invalid claim ID.",
            "danger"
        )

        return redirect(
            url_for(
                "claims.claims_list"
            )
        )

    claim = claims.find_one({
        "_id": object_id
    })

    if not claim:

        flash(
            "Claim not found.",
            "danger"
        )

        return redirect(
            url_for(
                "claims.claims_list"
            )
        )

    # -----------------------------------------------------
    # Latest prediction
    # -----------------------------------------------------

    prediction = predictions.find_one(
        {
            "$or": [
                {
                    "claim_object_id":
                        str(claim["_id"])
                },
                {
                    "claim_id":
                        claim.get("claim_id")
                }
            ]
        },
        sort=[
            (
                "prediction_date",
                -1
            )
        ]
    )

    return render_template(
        "view_claim.html",
        claim=claim,
        prediction=prediction
    )


# =========================================================
# EDIT CLAIM
# =========================================================

@claims_bp.route(
    "/claims/edit/<claim_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_claim(claim_id):

    object_id = get_object_id(
        claim_id
    )

    if not object_id:

        flash(
            "Invalid claim ID.",
            "danger"
        )

        return redirect(
            url_for(
                "claims.claims_list"
            )
        )

    claim = claims.find_one({
        "_id": object_id
    })

    if not claim:

        flash(
            "Claim not found.",
            "danger"
        )

        return redirect(
            url_for(
                "claims.claims_list"
            )
        )

    form = ClaimForm(
        data={
            "claim_id":
                claim.get(
                    "claim_id",
                    ""
                ),

            "claim_type":
                claim.get(
                    "claim_type",
                    ""
                ),

            "claim_amount":
                claim.get(
                    "claim_amount",
                    0
                ),

            "policy_limit":
                claim.get(
                    "policy_limit",
                    0
                ),

            "premium":
                claim.get(
                    "premium",
                    0
                ),

            "policy_age_days":
                claim.get(
                    "policy_age_days",
                    0
                ),

            "prior_claims":
                claim.get(
                    "prior_claims",
                    0
                ),

            "report_delay_days":
                claim.get(
                    "report_delay_days",
                    0
                ),

            "customer_age":
                claim.get(
                    "customer_age",
                    18
                ),

            "police_report":
                claim.get(
                    "police_report",
                    False
                )
        }
    )

    # -----------------------------------------------------
    # Process update
    # -----------------------------------------------------

    if form.validate_on_submit():

        new_claim_id = form.claim_id.data.strip()

        # -------------------------------------------------
        # Check duplicate Claim ID
        # -------------------------------------------------

        duplicate = claims.find_one({
            "claim_id": new_claim_id,
            "_id": {
                "$ne": object_id
            }
        })

        if duplicate:

            flash(
                "Another claim already uses this Claim ID.",
                "danger"
            )

            return render_template(
                "edit_claim.html",
                form=form,
                claim=claim
            )

        # -------------------------------------------------
        # Update claim
        # -------------------------------------------------

        update_data = {

            "claim_id":
                new_claim_id,

            "claim_type":
                form.claim_type.data.strip(),

            "claim_amount":
                form.claim_amount.data,

            "policy_limit":
                form.policy_limit.data,

            "premium":
                form.premium.data,

            "policy_age_days":
                form.policy_age_days.data,

            "prior_claims":
                form.prior_claims.data,

            "report_delay_days":
                form.report_delay_days.data,

            "customer_age":
                form.customer_age.data,

            "police_report":
                bool(
                    form.police_report.data
                ),

            "updated_at":
                datetime.utcnow()
        }

        claims.update_one(
            {
                "_id": object_id
            },
            {
                "$set": update_data
            }
        )

        flash(
            "Claim updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "claims.claims_list"
            )
        )

    return render_template(
        "edit_claim.html",
        form=form,
        claim=claim
    )


# =========================================================
# DELETE CLAIM
# =========================================================

@claims_bp.route(
    "/claims/delete/<claim_id>"
)
@login_required
def delete_claim(claim_id):

    object_id = get_object_id(
        claim_id
    )

    if not object_id:

        flash(
            "Invalid claim ID.",
            "danger"
        )

        return redirect(
            url_for(
                "claims.claims_list"
            )
        )

    claim = claims.find_one({
        "_id": object_id
    })

    if not claim:

        flash(
            "Claim not found.",
            "danger"
        )

        return redirect(
            url_for(
                "claims.claims_list"
            )
        )

    # -----------------------------------------------------
    # Delete claim
    # -----------------------------------------------------

    claims.delete_one({
        "_id": object_id
    })

    # -----------------------------------------------------
    # Delete associated predictions
    # -----------------------------------------------------

    predictions.delete_many({
        "$or": [
            {
                "claim_object_id":
                    str(object_id)
            },
            {
                "claim_id":
                    claim.get("claim_id")
            }
        ]
    })

    flash(
        "Claim deleted successfully.",
        "success"
    )

    return redirect(
        url_for(
            "claims.claims_list"
        )
    )