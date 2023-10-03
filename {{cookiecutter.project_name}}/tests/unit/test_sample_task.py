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
        # This is an example of how to set up a configuration file to test a task
        self.config = {
            "experiment": "/Shared/dbx/{{cookiecutter.package_name}}/dev_{{cookiecutter.package_name}}",
            "model_kwargs": {
                "learning_rate": 0.1,
                "max_iter": 1000,
                "tol": 0.0001,
            },
            "database": "dev",
            "input": {"table": "sample_transactions","path": ""},
            "output": {"table": "sample_data","path": ""},
            "execution_date": "2023-09-01",
        }

        # update conf file
        warehouse_dir = spark.conf.get("spark.hive.metastore.warehouse.dir")

        self.config["output"]["path"] = os.path.join(
            warehouse_dir, self.config["output"]["table"]
        )
        self.config["input"]["path"] = os.path.join(
            warehouse_dir, self.config["input"]["table"]
        )
        # create database
        create_database(spark, self.config)

        # This is an example of how to set up a SQL table with data to test a task
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
        df_transactions = pd.DataFrame(
            data={
                "sku": "314",
                "store": "S101",
                "date": [
                    "20210101",
                    "20210102",
                    "20210103",
                    "20210104",
                    "20210105",
                ],
                "sales": [10 * 10, 9 * 11, 8 * 12, 7 * 13, 6 * 14],
                "units": [10, 11, 12, 13, 14],
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
                self.config["input"]["table"],
            ),
            self.config["database"],
            self.config["input"]["table"],
            partition_cols=["date"],
        )

        # This is the excepted output of the task
        data = [
            (
                1.0,
                "foo",
                date(2023, 9, 1),
            ),
            (
                2.0,
                "bar",
                date(2023, 9, 1),
            ),
            (
                3.0,
                "baz",
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
    def test_task_output(
        self, setUp, spark: SparkSession
    ):
        # Check if output tables exist
        df = spark.read.format("delta").load(
            self.config["output"]["path"]
        )
        assert df.count() > 0

        # Check if output table is as expected
        assert_pyspark_df_equal(
            df, self.expected_df, atol=0.0
        )

    @pytest.mark.spark
    @pytest.mark.mlflow
    def test_mlflow_tracking_server_is_not_empty(self, setUp):
        experiment = mlflow.get_experiment_by_name(self.config["experiment"])
        assert experiment is not None

        runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
        assert runs.empty is False
