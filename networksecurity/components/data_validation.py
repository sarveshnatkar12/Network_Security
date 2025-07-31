import os
import sys
import pandas as pd
from scipy.stats import ks_2samp

from networksecurity.constant.training_pipeline import SCHEMA_FILE_PATH
from networksecurity.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact
from networksecurity.entity.config_entity import DataValidationConfig
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.utils.main_utils.utils import read_yaml_file, write_yaml_file


class DataValidation:
    def __init__(
        self,
        data_ingestion_artifact: DataIngestionArtifact,
        data_validation_config: DataValidationConfig
    ):
        try:
            self.data_ingestion_artifact = data_ingestion_artifact
            self.validation_config = data_validation_config
            self._schema_config = read_yaml_file(SCHEMA_FILE_PATH)
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    @staticmethod
    def read_data(file_path: str) -> pd.DataFrame:
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    # def validate_number_of_columns(self, df: pd.DataFrame) -> bool:
    #     try:
    #         expected = len(self._schema_config)
    #         found = len(df.columns)
    #         logging.info(f"Required number of columns: {expected}, found: {found}")
    #         return found == expected
    #     except Exception as e:
    #         raise NetworkSecurityException(e, sys)

    def validate_number_of_columns(self, dataframe: pd.DataFrame) -> bool:
        try:
            expected_columns = list(self._schema_config["columns"].keys())
            actual_columns = dataframe.columns.tolist()

            missing = set(expected_columns) - set(actual_columns)
            extra   = set(actual_columns) - set(expected_columns)

            if missing or extra:
                logging.error(f"❌ Schema Mismatch")
                logging.error(f"📄 Missing Columns: {missing}")
                logging.error(f"➕ Extra Columns: {extra}")
                return False

            logging.info("✅ Schema Validation Passed.")
            return True

        except Exception as e:
            raise NetworkSecurityException(e, sys)



    def detect_dataset_drift(
        self,
        base_df: pd.DataFrame,
        current_df: pd.DataFrame,
        threshold: float = 0.05
    ) -> bool:
        """
        Returns True if NO drift detected (all p-values >= threshold),
        False if any column shows p-value < threshold.
        Also writes out a YAML drift report.
        """
        try:
            report = {}
            drift_found = False

            for col in base_df.columns:
                stat = ks_2samp(base_df[col], current_df[col])
                p = float(stat.pvalue)
                has_drift = p < threshold
                report[col] = {
                    "p_value": p,
                    "drift_flag": has_drift
                }
                if has_drift:
                    drift_found = True

            # write report
            rpt_path = self.validation_config.drift_report_file_path
            os.makedirs(os.path.dirname(rpt_path), exist_ok=True)
            write_yaml_file(rpt_path, report, replace=True)

            if drift_found:
                logging.warning("Data drift detected.")
            else:
                logging.info("No data drift detected.")

            return not drift_found

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def initiate_data_validation(self) -> DataValidationArtifact:
        try:
            # 1) load ingested data
            train_df = self.read_data(self.data_ingestion_artifact.trained_file_path)
            test_df  = self.read_data(self.data_ingestion_artifact.test_file_path)

            # 2) validate schema
            if not self.validate_number_of_columns(train_df):
                raise NetworkSecurityException(
                    "Train dataframe does not contain all required columns", sys
                )
            if not self.validate_number_of_columns(test_df):
                raise NetworkSecurityException(
                    "Test dataframe does not contain all required columns", sys
                )

            # 3) check drift
            drift_ok = self.detect_dataset_drift(train_df, test_df)

            # 4) copy valid files to artifact locations
            os.makedirs(os.path.dirname(self.validation_config.valid_train_file_path), exist_ok=True)
            train_df.to_csv(self.validation_config.valid_train_file_path, index=False)

            os.makedirs(os.path.dirname(self.validation_config.valid_test_file_path), exist_ok=True)
            test_df.to_csv(self.validation_config.valid_test_file_path, index=False)

            # 5) build and return artifact
            return DataValidationArtifact(
                validation_status     = drift_ok,
                valid_train_file_path = self.validation_config.valid_train_file_path,
                valid_test_file_path  = self.validation_config.valid_test_file_path,
                invalid_train_file_path = None,
                invalid_test_file_path  = None,
                drift_report_file_path  = self.validation_config.drift_report_file_path,
            )

        except Exception as e:
            raise NetworkSecurityException(e, sys)
