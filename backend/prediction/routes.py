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


# ---------------------------------------
# Fraud Prediction
# ---------------------------------------
@prediction_bp.route(
    "/prediction",
    methods=["GET", "POST"]
)
@login_required
def prediction():

    # Create form
    form = PredictionForm()

    # ---------------------------------------
    # Populate claim dropdown
    # ---------------------------------------

    form.claim_id.choices = [
        (
            str(claim["_id"]),
            claim.get("claim_id", str(claim["_id"]))
        )
        for claim in claims.find()
    ]

    # ---------------------------------------
    # Process prediction
    # ---------------------------------------

    if form.validate_on_submit():

        # ---------------------------------------
        # Get selected claim
        # ---------------------------------------

        selected_claim = claims.find_one(
            {
                "_id": ObjectId(form.claim_id.data)
            }
        )

        # ---------------------------------------
        # Check claim exists
        # ---------------------------------------

        if not selected_claim:

            flash(
                "Selected claim was not found.",
                "danger"
            )

            return redirect(
                url_for("prediction.prediction")
            )

        # ---------------------------------------
        # Check required ML fields
        # ---------------------------------------

        required_fields = [
            "claim_amount",
            "policy_limit",
            "premium",
            "policy_age_days",
            "report_delay_days",
            "claim_type",
            "police_report"
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

        # ---------------------------------------
        # Prepare claim for ML model
        # ---------------------------------------

        claim_data = {

            "claim_amount":
                selected_claim["claim_amount"],

            "policy_limit":
                selected_claim["policy_limit"],

            "premium":
                selected_claim["premium"],

            "policy_age_days":
                selected_claim["policy_age_days"],

            "report_delay_days":
                selected_claim["report_delay_days"],

            "claim_type":
                selected_claim["claim_type"],

            "police_report":
                selected_claim["police_report"]
        }

        # ---------------------------------------
        # Run ML prediction
        # ---------------------------------------

        result = predict_risk(claim_data)

        # ---------------------------------------
        # Save prediction to MongoDB
        # ---------------------------------------

        predictions.insert_one({

            "claim_id":
                selected_claim["claim_id"],

            "claim_object_id":
                str(selected_claim["_id"]),

            "risk_score":
                result["risk_score"],

            "risk_percentage":
                result["risk_percentage"],

            "risk_level":
                result["risk_level"],

            "anomaly_score":
                result["anomaly_score"],

            "predicted_by":
                current_user.username,

            "prediction_date":
                datetime.utcnow()
        })

        # ---------------------------------------
        # Display result
        # ---------------------------------------

        return render_template(
            "prediction_result.html",
            claim=selected_claim,
            result=result
        )

    # ---------------------------------------
    # Display prediction page
    # ---------------------------------------

    return render_template(
        "prediction.html",
        form=form
    )
# ---------------------------------------
# Prediction History
# ---------------------------------------
@prediction_bp.route("/prediction/history")
@login_required
def prediction_history():

    all_predictions = list(
        predictions.find().sort(
            "prediction_date",
            -1
        )
    )

    return render_template(
        "prediction_history.html",
        predictions=all_predictions
    )