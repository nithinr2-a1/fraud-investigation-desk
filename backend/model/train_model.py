from pathlib import Path

import pandas as pd
import numpy as np
import joblib

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import IsolationForest


# ---------------------------------------
# Paths
# ---------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = BASE_DIR / "Insurance_Claims_Converted_Template.csv"

MODEL_PATH = BASE_DIR / "fraud_risk_model.pkl"

SCORES_PATH = BASE_DIR / "training_anomaly_scores.npy"


# ---------------------------------------
# Load Dataset
# ---------------------------------------

print("Loading dataset...")

df = pd.read_csv(DATASET_PATH)

print(f"Dataset loaded: {len(df):,} records")


# ---------------------------------------
# Feature Engineering
# ---------------------------------------

def prepare_features(data):

    x = data.copy()

    x["claim_to_limit_ratio"] = (
        x["claim_amount"]
        / x["policy_limit"].replace(0, np.nan)
    ).fillna(0)

    x["claim_to_premium_ratio"] = (
        x["claim_amount"]
        / x["premium"].replace(0, np.nan)
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
            "police_report"
        ]
    ]


X = prepare_features(df)


# ---------------------------------------
# Features
# ---------------------------------------

numeric_features = [
    "claim_amount",
    "policy_limit",
    "premium",
    "policy_age_days",
    "report_delay_days",
    "claim_to_limit_ratio",
    "claim_to_premium_ratio",
    "late_report_flag"
]

categorical_features = [
    "claim_type",
    "police_report"
]


# ---------------------------------------
# Preprocessor
# ---------------------------------------

preprocessor = ColumnTransformer(
    transformers=[
        (
            "num",
            "passthrough",
            numeric_features
        ),

        (
            "cat",
            OneHotEncoder(
                handle_unknown="ignore"
            ),
            categorical_features
        )
    ]
)


# ---------------------------------------
# ML Model
# ---------------------------------------

model = IsolationForest(
    n_estimators=300,
    contamination="auto",
    random_state=42,
    n_jobs=-1
)


# ---------------------------------------
# Pipeline
# ---------------------------------------

pipeline = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor
        ),

        (
            "model",
            model
        )
    ]
)


# ---------------------------------------
# Train
# ---------------------------------------

print("Training Isolation Forest model...")

pipeline.fit(X)


# ---------------------------------------
# Generate anomaly scores
# ---------------------------------------

decision_scores = pipeline.decision_function(X)

anomaly_scores = -decision_scores

sorted_scores = np.sort(anomaly_scores)


# ---------------------------------------
# Save Model
# ---------------------------------------

joblib.dump(
    pipeline,
    MODEL_PATH
)

np.save(
    SCORES_PATH,
    sorted_scores
)


print()
print("======================================")
print("ML MODEL TRAINING COMPLETED")
print("======================================")
print(f"Records       : {len(df):,}")
print(f"Features      : {len(X.columns)}")
print("Algorithm     : Isolation Forest")
print(f"Model saved   : {MODEL_PATH}")
print(f"Scores saved  : {SCORES_PATH}")
print("======================================")