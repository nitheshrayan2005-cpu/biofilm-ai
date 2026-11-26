
from pathlib import Path
import json
import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_DIR / "datasets" / "processed" / "biofilm_thickness.csv"
MODEL_DIR = PROJECT_DIR / "backend" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_FILE)

# One experimental trajectory = one channel-flow combination
df["experiment_group"] = (
    df["channel"].astype(str)
    + "_"
    + df["flow_rate_ul_min"].astype(str)
)

# Exclude unusual single-row trajectories for this first
# trajectory-level evaluation.
group_sizes = df.groupby("experiment_group").size()
valid_groups = group_sizes[group_sizes >= 10].index
df = df[df["experiment_group"].isin(valid_groups)].copy()

features = ["time", "flow_rate_ul_min", "channel"]
target = "AVEG"

X = df[features]
y = df[target]
groups = df["experiment_group"]

# Hold out complete trajectories
splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=0.25,
    random_state=42
)

train_idx, test_idx = next(
    splitter.split(X, y, groups=groups)
)

X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))
print("Training experiments:", groups.iloc[train_idx].nunique())
print("Testing experiments:", groups.iloc[test_idx].nunique())

# Preprocessing
preprocessor = ColumnTransformer([
    (
        "channel",
        OneHotEncoder(handle_unknown="ignore"),
        ["channel"]
    ),
    (
        "numeric",
        "passthrough",
        ["time", "flow_rate_ul_min"]
    )
])


models = {
    "Baseline": Pipeline([
        ("prep", preprocessor),
        ("model", DummyRegressor(strategy="mean"))
    ]),
    "Decision Tree": Pipeline([
        ("prep", preprocessor),
        ("model", DecisionTreeRegressor(
            max_depth=5,
            min_samples_leaf=5,
            random_state=42
        ))
    ])
}


results = {}

for name, model in models.items():
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = root_mean_squared_error(y_test, predictions)

    results[name] = {
        "MAE": float(mae),
        "RMSE": float(rmse)
    }

    print(f"\n{name}")
    print(f"MAE:  {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")

# Save model and metadata
best_model = models["Decision Tree"]
joblib.dump(
    best_model,
    MODEL_DIR / "biofilm_dt.joblib"
)

metadata = {
    "features": features,
    "target": target,
    "training_rows": len(X_train),
    "testing_rows": len(X_test),
    "training_experiments": int(
        groups.iloc[train_idx].nunique()
    ),
    "testing_experiments": int(
        groups.iloc[test_idx].nunique()
    ),
    "results": results,
    "evaluation": "GroupShuffleSplit by channel-flow experiment"
}

with open(MODEL_DIR / "metrics.json", "w") as f:
    json.dump(metadata, f, indent=2)

print("\nMODEL TRAINING COMPLETE")
print("Saved:", MODEL_DIR / "biofilm_dt.joblib")
print("Saved:", MODEL_DIR / "metrics.json")
print("\nNote: Model saved for experimentation.")
print("Do not treat this single split as final validation.")
