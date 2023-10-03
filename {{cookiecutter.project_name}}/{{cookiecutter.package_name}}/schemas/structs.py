from {{cookiecutter.package_name}}.schemas.names import (
    SampleDataColNames,
)
from pyspark.sql.types import (
    DateType,
    DoubleType,
    StringType,
    StructField,
    StructType,
)

SampleDataSchema = StructType(
    [
        StructField(SampleDataColNames.BAR.value, DoubleType(), True),
        StructField(SampleDataColNames.FOO.value, StringType(), False),
        StructField(SampleDataColNames.DT.value, DateType(), False),
    ]
)
