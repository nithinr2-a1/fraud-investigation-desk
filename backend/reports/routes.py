from flask import render_template
from flask_login import login_required

from . import reports_bp
from db import claims, cases, evidence, predictions


@reports_bp.route("/reports")
@login_required
def reports():

    # ==========================================================
    # BASIC STATISTICS
    # ==========================================================

    total_claims = claims.count_documents({})

    total_cases = cases.count_documents({})

    open_cases = cases.count_documents({
        "status": "Open"
    })

    closed_cases = cases.count_documents({
        "status": "Closed"
    })

    total_evidence = evidence.count_documents({})

    total_predictions = predictions.count_documents({})


    # ==========================================================
    # ML RISK DISTRIBUTION
    # ==========================================================

    high_risk = predictions.count_documents({
        "risk_level": "High"
    })

    medium_risk = predictions.count_documents({
        "risk_level": "Medium"
    })

    low_risk = predictions.count_documents({
        "risk_level": "Low"
    })


    # ==========================================================
    # RISK PERCENTAGES
    # ==========================================================

    if total_predictions > 0:

        high_risk_percentage = round(
            (high_risk / total_predictions) * 100,
            1
        )

        medium_risk_percentage = round(
            (medium_risk / total_predictions) * 100,
            1
        )

        low_risk_percentage = round(
            (low_risk / total_predictions) * 100,
            1
        )

    else:

        high_risk_percentage = 0
        medium_risk_percentage = 0
        low_risk_percentage = 0


    # ==========================================================
    # RECENT PREDICTIONS
    # ==========================================================

    recent_predictions = list(
        predictions.find(
            {},
            {
                "claim_id": 1,
                "risk_percentage": 1,
                "risk_level": 1,
                "prediction_date": 1,
                "_id": 0
            }
        )
        .sort(
            "prediction_date",
            -1
        )
        .limit(10)
    )


    chart_labels = [
        prediction.get(
            "claim_id",
            "Unknown"
        )
        for prediction in recent_predictions
    ]


    chart_values = [
        prediction.get(
            "risk_percentage",
            0
        )
        for prediction in recent_predictions
    ]


    # ==========================================================
    # CLAIM TYPE DISTRIBUTION
    # ==========================================================

    claim_type_pipeline = [
        {
            "$group": {
                "_id": "$claim_type",
                "count": {
                    "$sum": 1
                }
            }
        },
        {
            "$sort": {
                "count": -1
            }
        }
    ]


    claim_type_data = list(
        claims.aggregate(
            claim_type_pipeline
        )
    )


    claim_type_labels = [
        item.get("_id") or "Unknown"
        for item in claim_type_data
    ]


    claim_type_values = [
        item.get("count", 0)
        for item in claim_type_data
    ]


    # ==========================================================
    # CASE STATUS DISTRIBUTION
    # ==========================================================

    case_status_pipeline = [
        {
            "$group": {
                "_id": "$status",
                "count": {
                    "$sum": 1
                }
            }
        }
    ]


    case_status_data = list(
        cases.aggregate(
            case_status_pipeline
        )
    )


    case_status_labels = [
        item.get("_id") or "Unknown"
        for item in case_status_data
    ]


    case_status_values = [
        item.get("count", 0)
        for item in case_status_data
    ]


    # ==========================================================
    # ML MODEL PERFORMANCE
    # Based on the evaluated Isolation Forest model
    # ==========================================================

    true_negative = 3556
    false_positive = 144
    false_negative = 144
    true_positive = 156


    total_samples = (
        true_negative
        + false_positive
        + false_negative
        + true_positive
    )


    # ==========================================================
    # MODEL ACCURACY
    # ==========================================================

    accuracy = (
        (true_positive + true_negative)
        / total_samples
    ) * 100


    # ==========================================================
    # MODEL PRECISION
    # ==========================================================

    precision = (
        true_positive
        / (true_positive + false_positive)
    ) * 100


    # ==========================================================
    # MODEL RECALL
    # ==========================================================

    recall = (
        true_positive
        / (true_positive + false_negative)
    ) * 100


    # ==========================================================
    # F1 SCORE
    # ==========================================================

    f1_score = (
        2
        * precision
        * recall
        / (precision + recall)
    )


    # ==========================================================
    # SPECIFICITY
    # ==========================================================

    specificity = (
        true_negative
        / (true_negative + false_positive)
    ) * 100


    # ==========================================================
    # RENDER REPORTS
    # ==========================================================

    return render_template(
        "reports.html",

        total_claims=total_claims,
        total_cases=total_cases,
        open_cases=open_cases,
        closed_cases=closed_cases,
        total_evidence=total_evidence,
        total_predictions=total_predictions,

        high_risk=high_risk,
        medium_risk=medium_risk,
        low_risk=low_risk,

        high_risk_percentage=high_risk_percentage,
        medium_risk_percentage=medium_risk_percentage,
        low_risk_percentage=low_risk_percentage,

        chart_labels=chart_labels,
        chart_values=chart_values,

        claim_type_labels=claim_type_labels,
        claim_type_values=claim_type_values,

        case_status_labels=case_status_labels,
        case_status_values=case_status_values,

        true_negative=true_negative,
        false_positive=false_positive,
        false_negative=false_negative,
        true_positive=true_positive,

        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        specificity=specificity
    )