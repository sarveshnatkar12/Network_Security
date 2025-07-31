import sys, os
import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.impute import KNNImputer
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import FunctionTransformer

from networksecurity.constant.training_pipeline import TARGET_COLUMN, DATA_TRANSFORMATION_IMPUTER_PARAMS
from networksecurity.entity.artifact_entity import DataTransformationArtifact, DataValidationArtifact
from networksecurity.entity.config_entity import DataTransformationConfig
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.utils.main_utils.utils import save_numpy_array_data, save_object


# ✅ Top-level function to replace -1 with NaN (can be pickled)
def replace_minus1_with_nan(df):
    return df.replace(-1, np.nan)


class DataTransformation:
    def __init__(self,
                 data_validation_artifact: DataValidationArtifact,
                 data_transformation_config: DataTransformationConfig):
        try:
            self.data_validation_artifact = data_validation_artifact
            self.data_transformation_config = data_transformation_config
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    @staticmethod
    def read_data(file_path) -> pd.DataFrame:
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def get_data_transformer_object(self) -> ColumnTransformer:
        """
        Build a ColumnTransformer that:
         - For continuous columns: replaces -1 with NaN then KNN‐imputes
         - For all other columns: passes them through untouched
        """
        try:
            CONTINUOUS_FEATURES = [
                "Domain_registeration_length",
                "age_of_domain",
                "web_traffic",
                "Page_Rank",
                "Links_pointing_to_page",
                "Statistical_report"
            ]

            # ✅ Use the top-level function instead of lambda
            num_pipeline = Pipeline([
                ("mask_missing", FunctionTransformer(replace_minus1_with_nan)),
                ("imputer", KNNImputer(**DATA_TRANSFORMATION_IMPUTER_PARAMS))
            ])

            preprocessor = ColumnTransformer(
                transformers=[
                    ("num_impute", num_pipeline, CONTINUOUS_FEATURES),
                ],
                remainder="passthrough"  # all other features untouched
            )

            return preprocessor

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def initiate_data_transformation(self) -> DataTransformationArtifact:
        try:
            logging.info("Starting data transformation")
            train_df = self.read_data(self.data_validation_artifact.valid_train_file_path)
            test_df = self.read_data(self.data_validation_artifact.valid_test_file_path)

            y_train = train_df[TARGET_COLUMN].replace(-1, 0).to_numpy()
            y_test = test_df[TARGET_COLUMN].replace(-1, 0).to_numpy()

            X_train = train_df.drop(columns=[TARGET_COLUMN])
            X_test = test_df.drop(columns=[TARGET_COLUMN])

            preprocessor = self.get_data_transformer_object()
            preprocessor.fit(X_train)

            X_train_transformed = preprocessor.transform(X_train)
            X_test_transformed = preprocessor.transform(X_test)

            train_arr = np.c_[X_train_transformed, y_train]
            test_arr = np.c_[X_test_transformed, y_test]

            save_numpy_array_data(self.data_transformation_config.transformed_train_file_path,
                                  array=train_arr)
            save_numpy_array_data(self.data_transformation_config.transformed_test_file_path,
                                  array=test_arr)

            save_object(self.data_transformation_config.transformed_object_file_path,
                        preprocessor)
            save_object("final_model/preprocessor.pkl", preprocessor)

            return DataTransformationArtifact(
                transformed_object_file_path=self.data_transformation_config.transformed_object_file_path,
                transformed_train_file_path=self.data_transformation_config.transformed_train_file_path,
                transformed_test_file_path=self.data_transformation_config.transformed_test_file_path
            )

        except Exception as e:
            raise NetworkSecurityException(e, sys)
