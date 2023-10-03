import shutil
from pathlib import Path

from delta import DeltaTable
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import StructType
from pandas.testing import assert_frame_equal


def get_values_by_key_from_dict(d: dict, key: str):
    values = []

    def append_values_from_found_keys(d: dict, key_to_find: str) -> None:
        for key, value in d.items():
            if isinstance(value, dict):
                append_values_from_found_keys(value, key_to_find)
            if key == key_to_find:
                values.append(value)

    append_values_from_found_keys(d, key)
    return values


def create_database(spark: SparkSession, conf: dict) -> None:
    databases = get_values_by_key_from_dict(conf, "database")
    for database in databases:
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {database}")


def write_external_delta_table(
    spark: SparkSession,
    df: DataFrame,
    schema: StructType,
    path: str,
    database: str,
    table: str,
    partition_cols: list[str] = ["dt"],
) -> None:
    if Path(path).exists():
        shutil.rmtree(path)
    df = df.select(*schema.fieldNames())
    (
        DeltaTable.createOrReplace(spark)
        .tableName(f"{database}.{table}")
        .addColumns(schema)
        .partitionedBy(partition_cols)
        .location(path)
        .execute()
    )
    df.write.format("delta").partitionBy(*partition_cols).mode(
        "overwrite"
    ).option("partitionOverwriteMode", "dynamic").save(path)


def assert_pyspark_df_equal(
    expected_df: DataFrame, actual_df: DataFrame, **kwargs
) -> None:
    assert expected_df.dtypes == actual_df.dtypes, "Schema mismatch"  # nosec
    assert expected_df.count() == actual_df.count(), "Row count mismatch"  # nosec
    assert_frame_equal(expected_df.toPandas(), actual_df.toPandas(), **kwargs)
