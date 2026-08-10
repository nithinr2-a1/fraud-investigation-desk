from flask import render_template
from flask_login import login_required

from . import reports_bp
from db import claims, cases, evidence, predictions


@reports_bp.route("/reports")
@login_required
def reports():

    # -----------------------------
    # Basic counts
    # -----------------------------

    total_claims = claims.count_documents({})

    total_cases = cases.count_documents({})

    open_cases = cases.count_documents({
        "status": "Open"
    })

    total_evidence = evidence.count_documents({})

    total_predictions = predictions.count_documents({})

    # -----------------------------
    # Risk distribution
    # -----------------------------

    high_risk = predictions.count_documents({
        "risk_level": "High"
    })

    medium_risk = predictions.count_documents({
        "risk_level": "Medium"
    })

    low_risk = predictions.count_documents({
        "risk_level": "Low"
    })

    # -----------------------------
    # Recent predictions
    # -----------------------------

    recent_predictions = list(
        predictions.find()
        .sort("prediction_date", -1)
        .limit(10)
    )

    # -----------------------------
    # Render report
    # -----------------------------

    return render_template(
        "reports.html",
        total_claims=total_claims,
        total_cases=total_cases,
        open_cases=open_cases,
        total_evidence=total_evidence,
        total_predictions=total_predictions,
        high_risk=high_risk,
        medium_risk=medium_risk,
        low_risk=low_risk,
        recent_predictions=recent_predictions
    )