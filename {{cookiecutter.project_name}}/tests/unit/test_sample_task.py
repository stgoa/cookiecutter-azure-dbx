import pytest
from pyspark.sql import SparkSession
import os
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
    IntegerType,
)
import pandas as pd
import mlflow
from datetime import date

from {{cookiecutter.package_name}}.tasks.sample_task import SampleTask

from {{cookiecutter.package_name}}.schemas.structs import (
   SampleDataSchema
)
from {{cookiecutter.package_name}}.schemas.names import (
   SampleDataColNames
)
from tests.unit.utils import (
    assert_pyspark_df_equal,
    create_database,
    write_external_delta_table,
)


class TestSampleTask:
    @pytest.fixture
    def setUp(self, spark: SparkSession):
        self.config = {
            "experiment": "/Shared/dbx/{{cookiecutter.package_name}}/dev_{{cookiecutter.package_name}}",
            "model_kwargs": {
                "learning_rate": 0.1,
                "max_iter": 1000,
                "tol": 0.0001,
            },
            "database": "dev",
            "table": "sample_data",
            "path": "",
            "execution_date": "2023-09-01",
        }

        # update conf file
        warehouse_dir = spark.conf.get("spark.hive.metastore.warehouse.dir")

        self.config["path"] = os.path.join(
            warehouse_dir, "sample_data"
        )
        # create database
        create_database(spark, self.config)

        # Define the schema for the DataFrame
        self.transactions_schema = StructType(
            [
                StructField("sku", StringType(), True),
                StructField("store", StringType(), True),
                StructField("sales", StringType(), True),
                StructField("units", StringType(), True),
                StructField("date", StringType(), True),
            ]
        )

        # TRANSACTION DATA
        # 5 records (dates) for each sk_material
        df_transactions = pd.DataFrame(
            data={
                "sku": ["15010201"] * 5
                + ["15010202"] * 5
                + ["15010203"] * 5,
                "store": "158",
                "date": [
                    "20210101",
                    "20210102",
                    "20210103",
                    "20210104",
                    "20210105",
                ]
                * 3,
                "sales": [10 * 10, 9 * 11, 8 * 12, 7 * 13, 6 * 14]
                * 3,  # PxQ
                "units": [10, 11, 12, 13, 14] * 3,
            }
        )

        df_transactions = df_transactions[
            self.transactions_schema.fieldNames()
        ]

        self.df_transactions = spark.createDataFrame(
            df_transactions, schema=self.transactions_schema
        )

        # write dataframe to delta table
        write_external_delta_table(
            spark,
            self.df_transactions,
            self.transactions_schema,
            os.path.join(
                warehouse_dir,
                self.config["input"]["transactions_data"]["table"],
            ),
            self.config["database"],
            self.config["input"]["transactions_data"]["table"],
            partition_cols=["date"],
        )

        # Excepted output
        data = [
            (
                12.0,
                "101",
                date(2023, 9, 1),
            ),
            (
                12.0,
                "101",
                date(2023, 9, 1),
            ),
            (
                12.0,
                "101",
                date(2023, 9, 1),
            ),
        ]

        # Create expected output dataframe with
        self.expected_df = spark.createDataFrame(data, SampleDataSchema)

        # Create SampleTask object
        self.task = SampleTask(spark=spark, init_conf=self.config)

        # Run task
        self.task.launch()


    @pytest.mark.spark
    def test_output_ownelasticity(
        self, setUp, spark: SparkSession
    ):
        # Check if output tables exist
        df = spark.read.format("delta").load(
            self.config["path"]
        )
        assert df.count() > 0

        # Check if output table is as expected
        assert_pyspark_df_equal(
            df, self.expected_df, atol=0.1
        )  # since there is randomness in the algorithm, we use a tolerance of 0.1

    @pytest.mark.spark
    @pytest.mark.mlflow
    def test_mlflow_tracking_server_is_not_empty(self, setUp):
        experiment = mlflow.get_experiment_by_name(self.config["experiment"])
        assert experiment is not None

        runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
        assert runs.empty is False
