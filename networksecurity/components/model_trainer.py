import os, sys
from urllib.parse import urlparse

import mlflow
from sklearn.metrics import accuracy_score

from networksecurity.constant.training_pipeline import (
    MODEL_TRAINER_EXPECTED_SCORE,
    MODEL_TRAINER_OVER_FIITING_UNDER_FITTING_THRESHOLD
)
from networksecurity.entity.config_entity import ModelTrainerConfig
from networksecurity.entity.artifact_entity import (
    DataTransformationArtifact,
    ModelTrainerArtifact
)
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.utils.main_utils.utils import (
    load_object,
    save_object,
    load_numpy_array_data,
    evaluate_models
)
from networksecurity.utils.ml_utils.model.estimator import NetworkModel

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
    AdaBoostClassifier
)

class ModelTrainer:
    def __init__(
        self,
        model_trainer_config: ModelTrainerConfig,
        data_transformation_artifact: DataTransformationArtifact
    ):
        try:
            self.config = model_trainer_config
            self.data_artifact = data_transformation_artifact
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def _track_mlflow(self, name: str, metric_name: str, metric_value: float):
        mlflow.log_metric(f"{name}_{metric_name}", metric_value)

    def train_model(self, X_train, y_train, X_test, y_test) -> ModelTrainerArtifact:
        try:
            # 1) Define your candidate models
            models = {
                "Logistic Regression": LogisticRegression(max_iter=1000),
                "Decision Tree":        DecisionTreeClassifier(),
                "Random Forest":        RandomForestClassifier(),
                "Gradient Boosting":    GradientBoostingClassifier(),
                "AdaBoost":             AdaBoostClassifier()
            }

            # 2) Define your hyperparameter grids
            params = {
                "Logistic Regression": {
                    "penalty": ["l2"],
                    "C":       [0.01, 0.1, 1, 10],
                    "solver":  ["lbfgs"]
                },
                "Decision Tree": {
                    "max_depth":        [None, 5, 10, 20],
                    "min_samples_leaf": [1, 3, 5],
                    "criterion":        ["gini", "entropy"]
                },
                "Random Forest": {
                    "n_estimators":     [50, 100, 200],
                    "max_features":     ["sqrt", "log2", None],
                    "class_weight":     ["balanced"]
                },
                "Gradient Boosting": {
                    "n_estimators": [50, 100, 200],
                    "learning_rate": [0.1, 0.05, 0.01],
                    "subsample":     [0.6, 0.8, 1.0]
                },
                "AdaBoost": {
                    "n_estimators":   [50, 100, 200],
                    "learning_rate":  [0.1, 0.01, 0.001]
                }
            }

            # 3) Grid-search + re-fit
            report = evaluate_models(
                X_train, y_train, X_test, y_test,
                models=models, params=params
            )

            # 4) Select best model by highest test_score
            best_name = max(report, key=lambda k: report[k]["test_score"])
            best_info = report[best_name]
            best_model = best_info["best_estimator"]
            train_acc = best_info["train_score"]
            test_acc  = best_info["test_score"]

            logging.info(f"Best model: {best_name} → test_acc={test_acc:.3f}, train_acc={train_acc:.3f}")

            # 5) Enforce thresholds
            if test_acc < MODEL_TRAINER_EXPECTED_SCORE:
                raise NetworkSecurityException(
                    f"Test accuracy {test_acc:.3f} below expected {MODEL_TRAINER_EXPECTED_SCORE}", sys
                )
            gap = abs(train_acc - test_acc)
            if gap > MODEL_TRAINER_OVER_FIITING_UNDER_FITTING_THRESHOLD:
                raise NetworkSecurityException(
                    f"Generalization gap {gap:.3f} above threshold {MODEL_TRAINER_OVER_FIITING_UNDER_FITTING_THRESHOLD}", sys
                )

            # 6) Log to MLflow
            mlflow.set_registry_uri("https://dagshub.com/...")  # your URI
            with mlflow.start_run():
                self._track_mlflow(best_name, "train_accuracy", train_acc)
                self._track_mlflow(best_name, "test_accuracy",  test_acc)
                mlflow.sklearn.log_model(best_model, "model")

            # 7) Wrap & save final NetworkModel (preprocessor + estimator)
            preprocessor = load_object(self.data_artifact.transformed_object_file_path)
            network_model = NetworkModel(preprocessor=preprocessor, model=best_model)

            os.makedirs(os.path.dirname(self.config.trained_model_file_path), exist_ok=True)
            save_object(self.config.trained_model_file_path, network_model)
            save_object("final_model/model.pkl", best_model)

            return ModelTrainerArtifact(
                trained_model_file_path=self.config.trained_model_file_path,
                train_metric_artifact=None,
                test_metric_artifact=None
            )

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def initiate_model_trainer(self) -> ModelTrainerArtifact:
        try:
            train_arr = load_numpy_array_data(self.data_artifact.transformed_train_file_path)
            test_arr  = load_numpy_array_data(self.data_artifact.transformed_test_file_path)

            X_train, y_train = train_arr[:, :-1], train_arr[:, -1]
            X_test,  y_test  = test_arr[:, :-1],  test_arr[:, -1]

            return self.train_model(X_train, y_train, X_test, y_test)

        except Exception as e:
            raise NetworkSecurityException(e, sys)
