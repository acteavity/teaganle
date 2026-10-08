"""Week 2 lab: train a RandomForest on the digits dataset and track it with MLflow."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import mlflow
from sklearn.datasets import load_digits
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

# ---- Hyperparameters: change these between runs ----
N_ESTIMATORS = 200
MAX_DEPTH = None
RANDOM_STATE = 42

mlflow.set_experiment("week2-lab")


def main():
    X, y = load_digits(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    with mlflow.start_run():
        model = RandomForestClassifier(
            n_estimators=N_ESTIMATORS,
            max_depth=MAX_DEPTH,
            random_state=RANDOM_STATE,
        )
        mlflow.log_param("n_estimators", N_ESTIMATORS)
        mlflow.log_param("max_depth", MAX_DEPTH)
        mlflow.log_param("random_state", RANDOM_STATE)

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average="macro")
        recall = recall_score(y_test, y_pred, average="macro")
        f1 = f1_score(y_test, y_pred, average="macro")

        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("precision", precision)
        mlflow.log_metric("recall", recall)
        mlflow.log_metric("f1", f1)

        print(f"accuracy:  {accuracy:.4f}")
        print(f"precision: {precision:.4f}")
        print(f"recall:    {recall:.4f}")
        print(f"f1:        {f1:.4f}")

        fig, ax = plt.subplots(figsize=(6, 6))
        ConfusionMatrixDisplay.from_predictions(y_test, y_pred, ax=ax)
        fig.savefig("confusion_matrix.png")
        mlflow.log_artifact("confusion_matrix.png")
        plt.close(fig)


if __name__ == "__main__":
    main()
