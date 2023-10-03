import json
import yaml
import logging
from datetime import date, datetime
import mlflow
import pyspark.sql.functions as F

from delta.tables import DeltaTable
from pyspark.sql.dataframe import DataFrame

from {{cookiecutter.package_name}} import SETTINGS
from {{cookiecutter.package_name}}.schemas.structs import (
   SampleDataSchema
)
from {{cookiecutter.package_name}}.schemas.names import (
   SampleDataColNames
)
from {{cookiecutter.package_name}}.common import Task


# suppress py4j logging
logging.getLogger("py4j").setLevel(logging.ERROR)


class SampleTask(Task):
    def __init__(self, spark=None, init_conf=None):
        super().__init__(spark, init_conf)
        self.spark.sql(f'CREATE SCHEMA IF NOT EXISTS {self.conf["database"]}')
        self._update_conf()
        self.logger.info(f"Configuration: \n{yaml.dump(self.conf)}")

    def _update_conf(self) -> None:
        """Updates the configuration with the execution date"""
        if "execution_date" not in self.conf:
            execution_date = date.today()
        else:
            execution_date = datetime.strptime(
                self.conf["execution_date"], "%Y-%m-%d"
            ).date()

        self.conf["execution_date"] = execution_date  # type: datetime

    def _compute_data(self) -> DataFrame:
        self.logger.info("compute data subtask started")

        # create sample data
        rows = [
            (1, "foo", date(2020, 1, 1)),
            (2, "bar", date(2020, 1, 1)),
            (3, "baz", date(2020, 1, 1)),
        ]

        # create dataframe
        df = self.spark.createDataFrame(rows, SampleDataSchema)

        self.logger.info("compute data subtask finished")
        return df

    def _write_output(
        self,
        df: DataFrame,
    ) -> None:
        self.logger.info("write output subtask started")

        schema = SampleDataSchema
        database = self.conf["database"]
        table_name = self.conf["table_name"]
        path = self.conf["path"]

        # add execution date
        df = df.withColumn("dt", F.lit(self.conf["execution_date"])).select(
            *schema.fieldNames()
        )

        self.logger.info(
            f"Writing to {database}.{table_name} at {path} with schema {df.schema}"
        )

        df = self.spark.createDataFrame(df.rdd, schema)

        # register table in metastore if it doesn't exist
        (
            DeltaTable.createIfNotExists(self.spark)
            .tableName(f"{database}.{table_name}")
            .addColumns(schema)
            .partitionedBy("dt")
            .location(path)
            .execute()
        )

        # write to delta table
        df.write.format("delta").partitionBy("dt").mode("overwrite").option(
            "mergeSchema", "true"
        ).option("partitionOverwriteMode", "dynamic").save(path)

        self.logger.info("write output subtask finished")

    def _log_metrics(self, df: DataFrame) -> None:
        self.logger.info("Logging metrics to mlflow")

        metric = df.agg(F.mean(SampleDataColNames.BAR.value)).collect()[
            0
        ][0]
        self.logger.info(f"avg value of column {SampleDataColNames.BAR.value} : {metric}")

        if metric is None:
            metric = +1.0
            self.logger.warning(
                f"avg value of column {SampleDataColNames.BAR.value} is None, setting it to {metric} to avoid errors"
            )

        with mlflow.start_run(run_name=self.__class__.__name__):
            # log parameters
            mlflow.log_params(self.conf["model_kwargs"])
            mlflow.set_tags(self.conf)
            # log metrics with current parameters
            mlflow.log_metric(f"avg_{SampleDataColNames.BAR.value}", metric)

        self.logger.info("Metrics logged to mlflow")

    def launch(self):
        """Launches the task"""
        self.logger.info("Launching SampleTaskTask")
        mlflow.set_experiment(self.conf["experiment"])

        df_sample = self._compute_data().cache()
        self._write_output(df_sample)
        self._log_metrics(df_sample)
        self.logger.info("SampleTask finished")


def entrypoint():
    task = SampleTask()
    task.launch()
