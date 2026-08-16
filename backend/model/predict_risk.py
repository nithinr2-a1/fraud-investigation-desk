import numpy as np
import pandas as pd
import joblib
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "fraud_risk_model.pkl"
SCORES_PATH = BASE_DIR / "training_anomaly_scores.npy"


# =========================================================
# LOAD TRAINED ML MODEL
# =========================================================

model = joblib.load(MODEL_PATH)

sorted_scores = np.load(SCORES_PATH)


# =========================================================
# NORMALIZE POLICE REPORT
# =========================================================

def normalize_police_report(value):

    """
    Convert different police_report representations
    into the values expected by the trained ML model.

    Expected model values:

        "yes"
        "no"
    """

    # Boolean values
    if isinstance(value, (bool, np.bool_)):

        return "yes" if bool(value) else "no"

    # Numeric values
    if isinstance(value, (int, float, np.integer, np.floating)):

        return "yes" if value == 1 else "no"

    # String values
    if isinstance(value, str):

        value = value.strip().lower()

        if value in [
            "yes",
            "y",
            "true",
            "1",
            "available"
        ]:

            return "yes"

        if value in [
            "no",
            "n",
            "false",
            "0",
            "not available"
        ]:

            return "no"

    # Default
    return "no"


# =========================================================
# PREPARE FEATURES
# =========================================================

def prepare_features(data):

    x = data.copy()

    # -----------------------------------------------------
    # Claim to Policy Limit Ratio
    # -----------------------------------------------------

    x["claim_to_limit_ratio"] = (
        x["claim_amount"]
        /
        x["policy_limit"].replace(
            0,
            np.nan
        )
    ).fillna(0)

    # -----------------------------------------------------
    # Claim to Premium Ratio
    # -----------------------------------------------------

    x["claim_to_premium_ratio"] = (
        x["claim_amount"]
        /
        x["premium"].replace(
            0,
            np.nan
        )
    ).fillna(0)

    # -----------------------------------------------------
    # Late Report Flag
    # -----------------------------------------------------

    x["late_report_flag"] = (
        x["report_delay_days"] > 2
    ).astype(int)

    # -----------------------------------------------------
    # Normalize Police Report
    # -----------------------------------------------------

    x["police_report"] = (
        x["police_report"]
        .apply(normalize_police_report)
    )

    # -----------------------------------------------------
    # Return features in EXACT training order
    # -----------------------------------------------------

    return x[
        [
            "claim_amount",
            "policy_limit",
            "premium",
            "policy_age_days",
            "report_delay_days",
            "claim_to_limit_ratio",
            "claim_to_premium_ratio",
            "late_report_flag",
            "claim_type",
            "police_report",
        ]
    ]


# =========================================================
# PREDICT FRAUD RISK
# =========================================================

def predict_risk(claim):

    # -----------------------------------------------------
    # Convert claim to DataFrame
    # -----------------------------------------------------

    data = pd.DataFrame([claim])

    # -----------------------------------------------------
    # Prepare ML features
    # -----------------------------------------------------

    features = prepare_features(data)

    # -----------------------------------------------------
    # Run Isolation Forest
    # -----------------------------------------------------

    decision = float(
        model.decision_function(features)[0]
    )

    # Isolation Forest:
    # Lower decision function = more anomalous
    anomaly_score = -decision

    # -----------------------------------------------------
    # Compare against training population
    # -----------------------------------------------------

    percentile = (
        np.searchsorted(
            sorted_scores,
            anomaly_score,
            side="right"
        )
        /
        len(sorted_scores)
    )

    # -----------------------------------------------------
    # Risk Score
    # -----------------------------------------------------

    risk_score = round(
        float(
            np.clip(
                percentile,
                0,
                1
            )
        ),
        4
    )

    # -----------------------------------------------------
    # Risk Level
    # -----------------------------------------------------

    if risk_score >= 0.80:

        risk_level = "High"

    elif risk_score >= 0.50:

        risk_level = "Medium"

    else:

        risk_level = "Low"

    # -----------------------------------------------------
    # Return prediction result
    # -----------------------------------------------------

    return {

        "risk_score":
            risk_score,

        "risk_percentage":
            round(
                risk_score * 100,
                2
            ),

        "risk_level":
            risk_level,

        "anomaly_score":
            anomaly_score
    }


# =========================================================
# TEST PREDICTION
# =========================================================

if __name__ == "__main__":

    example = {

        "claim_amount": 11586,

        "policy_limit": 23172,

        "premium": 1116,

        "policy_age_days": 279,

        "report_delay_days": 2,

        "claim_type": "Health",

        "police_report": "yes"
    }

    print(
        predict_risk(example)
    )