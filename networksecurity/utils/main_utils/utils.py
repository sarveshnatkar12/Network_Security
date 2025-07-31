import os, sys, yaml, numpy as np
from joblib import dump, load
from sklearn.model_selection import GridSearchCV
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

def read_yaml_file(file_path: str) -> dict:
    try:
        with open(file_path,"rb") as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise NetworkSecurityException(e, sys)

def write_yaml_file(file_path: str, content: object, replace: bool = False) -> None:
    try:
        if replace and os.path.exists(file_path):
            os.remove(file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            yaml.dump(content, f)
    except Exception as e:
        raise NetworkSecurityException(e, sys)

def save_numpy_array_data(file_path: str, array: np.array):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            np.save(f, array)
    except Exception as e:
        raise NetworkSecurityException(e, sys)

def load_numpy_array_data(file_path: str) -> np.array:
    try:
        with open(file_path, "rb") as f:
            return np.load(f)
    except Exception as e:
        raise NetworkSecurityException(e, sys)

def save_object(file_path: str, obj: object) -> None:
    try:
        logging.info(f"Saving object to {file_path}")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        dump(obj, file_path)
    except Exception as e:
        raise NetworkSecurityException(e, sys)

def load_object(file_path: str) -> object:
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"{file_path} not found")
        return load(file_path)
    except Exception as e:
        raise NetworkSecurityException(e, sys)

def evaluate_models(X_train, y_train, X_test, y_test, models: dict, params: dict) -> dict:
    """
    For each model:
     - runs GridSearchCV(cv=5, scoring='accuracy')
     - refits on full train set
     - returns dict:
         { model_name: {'train_score': <acc>, 'test_score': <acc>} }
    """
    try:
        report = {}
        for name, model in models.items():
            grid = params.get(name, {})
            gs = GridSearchCV(
                estimator=model,
                param_grid=grid,
                cv=5,
                scoring="accuracy",
                n_jobs=-1,
            )
            gs.fit(X_train, y_train)

            # best = gs.best_estimator_
            best = CalibratedClassifierCV(gs.best_estimator_, method='sigmoid', cv=3)
            # re-fit on entire training data
            best.fit(X_train, y_train)

            y_train_pred = best.predict(X_train)
            y_test_pred  = best.predict(X_test)

            train_acc = accuracy_score(y_train, y_train_pred)
            test_acc  = accuracy_score(y_test,  y_test_pred)

            report[name] = {
                "train_score": train_acc,
                "test_score":  test_acc,
                "best_estimator": best
            }

        return report

    except Exception as e:
        raise NetworkSecurityException(e, sys)
