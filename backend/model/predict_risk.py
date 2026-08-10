import numpy as np
import pandas as pd
import joblib
from pathlib import Path


# ---------------------------------------
# Paths
# ---------------------------------------

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "fraud_risk_model.pkl"
SCORES_PATH = BASE_DIR / "training_anomaly_scores.npy"


# ---------------------------------------
# Load trained ML model
# ---------------------------------------

model = joblib.load(MODEL_PATH)
sorted_scores = np.load(SCORES_PATH)


# ---------------------------------------
# Prepare features
# ---------------------------------------

def prepare_features(data):

    x = data.copy()

    x["claim_to_limit_ratio"] = (
        x["claim_amount"] /
        x["policy_limit"].replace(0, np.nan)
    ).fillna(0)

    x["claim_to_premium_ratio"] = (
        x["claim_amount"] /
        x["premium"].replace(0, np.nan)
    ).fillna(0)

    x["late_report_flag"] = (
        x["report_delay_days"] > 2
    ).astype(int)

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


# ---------------------------------------
# Predict fraud risk
# ---------------------------------------

def predict_risk(claim):

    data = pd.DataFrame([claim])

    features = prepare_features(data)

    decision = float(
        model.decision_function(features)[0]
    )

    anomaly_score = -decision

    # Compare against training population
    percentile = (
        np.searchsorted(
            sorted_scores,
            anomaly_score,
            side="right"
        )
        / len(sorted_scores)
    )

    risk_score = round(
        float(np.clip(percentile, 0, 1)),
        4
    )

    if risk_score >= 0.80:
        risk_level = "High"

    elif risk_score >= 0.50:
        risk_level = "Medium"

    else:
        risk_level = "Low"

    return {
        "risk_score": risk_score,
        "risk_percentage": round(
            risk_score * 100,
            2
        ),
        "risk_level": risk_level,
        "anomaly_score": anomaly_score,
    }


# ---------------------------------------
# Test prediction
# ---------------------------------------

if __name__ == "__main__":

    example = {
        "claim_amount": 11586,
        "policy_limit": 23172,
        "premium": 1116,
        "policy_age_days": 279,
        "report_delay_days": 2,
        "claim_type": "Health",
        "police_report": "yes",
    }

    print(predict_risk(example))