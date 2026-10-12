"""Train a SYNTHETIC stand-in model with the same pipeline structure as code.ipynb.

For tests and local smoke runs only. It is trained on randomly generated rows, so its predictions mean
nothing. Never deploy it. The real model is exported from code.ipynb as Mental_Health_Model2.pkl.

Usage (from backend/):  python -m scripts.make_dev_model [output_path]
"""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, OrdinalEncoder, StandardScaler

SKEWED = ["Study_Hours"]
NUMERIC = ["Age", "Avg_Daily_Usage_Hours", "Daily_Unlocks", "Physical_Activity_Hours", "Sleep_Hours_Per_Night"]
ORDINAL = ["Stress_Level"]
NOMINAL = ["Gender", "Academic_Level", "Most_Used_Platform", "Purpose_Of_Use", "Grouped_country"]

GENDERS = ["Female", "Male"]
LEVELS = ["High School", "Undergraduate", "Graduate"]
PLATFORMS = [
    "Instagram",
    "TikTok",
    "Facebook",
    "LinkedIn",
    "YouTube",
    "Twitter",
    "Snapchat",
    "WhatsApp",
    "LINE",
    "VKontakte",
    "KakaoTalk",
    "WeChat",
]
PURPOSES = ["Networking", "Education", "Entertainment"]
COUNTRIES = ["India", "USA", "Canada", "Australia", "UK", "Germany", "Mexico", "Turkey", "France", "Other"]
STRESS = ["Low", "Medium", "High", "Very High"]


def synthetic_frame(rows: int = 600, seed: int = 0) -> tuple[pd.DataFrame, pd.Series]:
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame(
        {
            "Study_Hours": rng.uniform(0.3, 8.3, rows).round(1),
            "Age": rng.integers(18, 25, rows),
            "Avg_Daily_Usage_Hours": rng.uniform(1.0, 8.8, rows).round(1),
            "Daily_Unlocks": rng.integers(62, 274, rows),
            "Physical_Activity_Hours": rng.uniform(0.0, 4.1, rows).round(1),
            "Sleep_Hours_Per_Night": rng.uniform(3.6, 9.9, rows).round(1),
            "Stress_Level": rng.choice(STRESS, rows),
            "Gender": rng.choice(GENDERS, rows),
            "Academic_Level": rng.choice(LEVELS, rows),
            "Most_Used_Platform": rng.choice(PLATFORMS, rows),
            "Purpose_Of_Use": rng.choice(PURPOSES, rows),
            "Grouped_country": rng.choice(COUNTRIES, rows),
        }
    )
    stress_rank = frame["Stress_Level"].map({s: i for i, s in enumerate(STRESS)})
    target = (
        6.2
        + 0.4 * (frame["Sleep_Hours_Per_Night"] - 6.6)
        - 0.25 * (frame["Avg_Daily_Usage_Hours"] - 5.0)
        + 0.15 * frame["Physical_Activity_Hours"]
        - 0.5 * stress_rank
        + rng.normal(0, 0.3, rows)
    ).clip(3.6, 9.4)
    return frame, target


def build_dev_pipeline() -> Pipeline:
    """Same step and transformer names as the notebook, so the backend's introspection is exercised."""
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "Skewed_Pipeline",
                Pipeline([("log_transform", FunctionTransformer(np.log1p)), ("scale", StandardScaler())]),
                SKEWED,
            ),
            ("Plain_Numeric", Pipeline([("scale", StandardScaler())]), NUMERIC),
            ("Ordinal", Pipeline([("encode", OrdinalEncoder(categories=[STRESS]))]), ORDINAL),
            ("Normal", Pipeline([("encode", OneHotEncoder(handle_unknown="ignore"))]), NOMINAL),
        ]
    )
    forest = RandomForestRegressor(n_estimators=30, random_state=0)
    return Pipeline(steps=[("preprocessor", preprocessor), ("random forest", forest)])


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("models/DEV_SYNTHETIC_model.pkl")
    output.parent.mkdir(parents=True, exist_ok=True)
    features, target = synthetic_frame()
    pipeline = build_dev_pipeline().fit(features, target)
    joblib.dump(pipeline, output)
    print(f"Wrote SYNTHETIC dev model to {output} (not a real model; do not deploy).")


if __name__ == "__main__":
    main()
