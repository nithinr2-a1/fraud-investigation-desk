from datetime import datetime

from flask import (
    render_template,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_required,
    current_user
)

from bson import ObjectId

from . import prediction_bp
from .forms import PredictionForm

from db import claims, predictions

from model.predict_risk import predict_risk


# =========================================================
# Fraud Prediction
# =========================================================

@prediction_bp.route(
    "/prediction",
    methods=["GET", "POST"]
)
@login_required
def prediction():

    # -----------------------------------------------------
    # Create form
    # -----------------------------------------------------

    form = PredictionForm()

    # -----------------------------------------------------
    # Populate claim dropdown
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
    # Process prediction
    # -----------------------------------------------------

    if form.validate_on_submit():

        # -------------------------------------------------
        # Get selected claim
        # -------------------------------------------------

        try:

            selected_claim = claims.find_one(
                {
                    "_id": ObjectId(form.claim_id.data)
                }
            )

        except Exception:

            flash(
                "Invalid claim selection.",
                "danger"
            )

            return redirect(
                url_for("prediction.prediction")
            )

        # -------------------------------------------------
        # Check claim exists
        # -------------------------------------------------

        if not selected_claim:

            flash(
                "Selected claim was not found.",
                "danger"
            )

            return redirect(
                url_for("prediction.prediction")
            )

        # -------------------------------------------------
        # Required ML fields
        # -------------------------------------------------

        required_fields = [
            "claim_amount",
            "policy_limit",
            "premium",
            "policy_age_days",
            "report_delay_days",
            "claim_type"
        ]

        missing_fields = [
            field
            for field in required_fields
            if field not in selected_claim
        ]

        if missing_fields:

            flash(
                "Claim is missing ML fields: "
                + ", ".join(missing_fields),
                "danger"
            )

            return redirect(
                url_for("prediction.prediction")
            )

        # -------------------------------------------------
        # Prepare claim data for ML model
        # -------------------------------------------------

        claim_data = {

            "claim_amount":
                selected_claim.get(
                    "claim_amount",
                    0
                ),

            "policy_limit":
                selected_claim.get(
                    "policy_limit",
                    0
                ),

            "premium":
                selected_claim.get(
                    "premium",
                    0
                ),

            "policy_age_days":
                selected_claim.get(
                    "policy_age_days",
                    0
                ),

            "report_delay_days":
                selected_claim.get(
                    "report_delay_days",
                    0
                ),

            "claim_type":
                selected_claim.get(
                    "claim_type",
                    "Unknown"
                ),

            "police_report":
                selected_claim.get(
                    "police_report",
                    False
                )
        }

        # -------------------------------------------------
        # Run ML prediction
        # -------------------------------------------------

        result = predict_risk(
            claim_data
        )

        # -------------------------------------------------
        # Save prediction to MongoDB
        # -------------------------------------------------

        predictions.insert_one({

            "claim_id":
                selected_claim.get(
                    "claim_id",
                    str(selected_claim["_id"])
                ),

            "claim_object_id":
                str(selected_claim["_id"]),

            "risk_score":
                result.get(
                    "risk_score",
                    0
                ),

            "risk_percentage":
                result.get(
                    "risk_percentage",
                    0
                ),

            "risk_level":
                result.get(
                    "risk_level",
                    "Unknown"
                ),

            "anomaly_score":
                result.get(
                    "anomaly_score",
                    0
                ),

            "predicted_by":
                current_user.username,

            "prediction_date":
                datetime.utcnow()
        })

        # -------------------------------------------------
        # Display prediction result
        # -------------------------------------------------

        return render_template(
            "prediction_result.html",
            claim=selected_claim,
            result=result
        )

    # -----------------------------------------------------
    # Display prediction page
    # -----------------------------------------------------

    return render_template(
        "prediction.html",
        form=form
    )


# =========================================================
# Prediction History
# =========================================================

@prediction_bp.route(
    "/prediction/history"
)
@login_required
def prediction_history():

    # -----------------------------------------------------
    # Get latest predictions first
    # -----------------------------------------------------

    all_predictions = list(
        predictions.find().sort(
            "prediction_date",
            -1
        )
    )

    # -----------------------------------------------------
    # Display history
    # -----------------------------------------------------

    return render_template(
        "prediction_history.html",
        predictions=all_predictions
    )