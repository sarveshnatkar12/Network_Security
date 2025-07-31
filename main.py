# main.py

import sys

from networksecurity.components.data_ingestion     import DataIngestion
from networksecurity.components.data_validation    import DataValidation
from networksecurity.components.data_transformation import DataTransformation
from networksecurity.components.model_trainer      import ModelTrainer

from networksecurity.entity.config_entity import (
    TrainingPipelineConfig,
    DataIngestionConfig,
    DataValidationConfig,
    DataTransformationConfig,
    ModelTrainerConfig
)

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger      import logging


if __name__ == "__main__":
    try:
        # bootstrap configs
        pipeline_cfg = TrainingPipelineConfig()

        # data ingestion
        ing_cfg = DataIngestionConfig(pipeline_cfg)
        ingestion = DataIngestion(ing_cfg)
        logging.info("Starting data ingestion")
        ingestion_artifact = ingestion.initiate_data_ingestion()
        logging.info(f"Ingestion complete: {ingestion_artifact}")

        # data validation
        val_cfg = DataValidationConfig(pipeline_cfg)
        validation = DataValidation(ingestion_artifact, val_cfg)
        logging.info("Starting data validation")
        validation_artifact = validation.initiate_data_validation()
        logging.info(f"Validation complete: {validation_artifact}")

        # halt if validation failed
        if not validation_artifact.validation_status:
            raise NetworkSecurityException(
                "Data Validation failed: drift or schema mismatch detected.", sys
            )

        # data transformation
        trans_cfg = DataTransformationConfig(pipeline_cfg)
        transform = DataTransformation(validation_artifact, trans_cfg)
        logging.info("Starting data transformation")
        transformation_artifact = transform.initiate_data_transformation()
        logging.info(f"Transformation complete: {transformation_artifact}")

        # model training
        trainer_cfg = ModelTrainerConfig(pipeline_cfg)
        trainer = ModelTrainer(trainer_cfg, transformation_artifact)
        logging.info("Starting model training")
        trainer_artifact = trainer.initiate_model_trainer()
        logging.info(f"Model training complete: {trainer_artifact}")

    except Exception as e:
        raise NetworkSecurityException(e, sys)
