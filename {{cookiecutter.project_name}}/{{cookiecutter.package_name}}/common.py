from abc import ABC, abstractmethod
from argparse import ArgumentParser
import json
from typing import Dict, Any
import yaml
import pathlib
from pyspark.sql import SparkSession
import sys

from typing import Optional
from pydantic import BaseModel, validator

def get_dbutils(
    spark: SparkSession,
):  # please note that this function is used in mocking by its name
    try:
        from pyspark.dbutils import DBUtils  # noqa

        if "dbutils" not in locals():
            utils = DBUtils(spark)
            return utils
        else:
            return locals().get("dbutils")
    except ImportError:
        return None

class OptionalParams(BaseModel):
    env : Optional[str] = None
    # add your optional parameters here
    foo : Optional[str] = None
    bar : Optional[str] = None

    @validator(
        "env",
    )
    def validate_environment(cls, value):
        if value is None:
            return value
        if value not in {"dev", "prod", "staging"}:
            raise ValueError(
                f"Invalid value {value} for environment. Must be one of dev, prod, staging"
            )
        return value

    @classmethod
    def add_fields_as_arguments(cls, parser: ArgumentParser):
        for field_name, field_type in cls.__annotations__.items():
            if (
                hasattr(field_type, "__args__")
                and type(None) in field_type.__args__
            ):
                # Handle Optional[T] types
                parser.add_argument(
                    f"--{field_name}",
                    type=field_type.__args__[0],
                    required=False,
                )
            else:
                # Handle non-Optional[T] types
                # this raises an ArgumentError if the field is not provided
                parser.add_argument(
                    f"--{field_name}", type=field_type, required=True
                )

class Task(ABC):
    """
    This is an abstract class that provides handy interfaces to implement
    workloads (e.g. jobs or job tasks).
    Create a child from this class and implement the abstract launch method.
    Class provides access to the following useful objects:
    * self.spark is a SparkSession
    * self.dbutils provides access to the DBUtils
    * self.logger provides access to the Spark-compatible logger
    * self.conf provides access to the parsed configuration of the job
    """

    def __init__(self, spark=None, init_conf=None):
        self.spark = self._prepare_spark(spark)
        self.logger = self._prepare_logger()
        self.dbutils = self.get_dbutils()
        if init_conf:
            self.conf = init_conf
        else:
            # parse arguments and set configuration
            self._set_config()
        self._log_conf()

    @staticmethod
    def _prepare_spark(spark) -> SparkSession:
        if not spark:
            return SparkSession.builder.getOrCreate()
        else:
            return spark

    def get_dbutils(self):
        utils = get_dbutils(self.spark)

        if not utils:
            self.logger.warn("No DBUtils defined in the runtime")
        else:
            self.logger.info("DBUtils class initialized")

        return utils

    def _set_config(self):
        self.logger.info("Reading configuration from --conf-file job option")
        p = ArgumentParser()
        # this are required arguments
        p.add_argument("--conf-file", required=False, type=str)
        p.add_argument("--named_parameters", required=False, type=str)
        # this are optional arguments
        OptionalParams.add_fields_as_arguments(p)
        # parse arguments
        namespace = p.parse_args(sys.argv[1:])
        # transform namespace to dict
        args = vars(namespace)
        # parse the optional arguments using pydantic's BaseModel
        input_params = OptionalParams(**args)

        # get the conf file path and env
        conf_file = args.get("conf_file")

        if not conf_file:
            self.logger.info(
                "No conf file was provided, setting config to empty dict."
                "Please override configuration in subclass init method"
            )
            self.conf = {}
            return
        self.logger.info(
            f"Conf file was provided, reading config from {conf_file}"
        )
        self.conf = self._read_config(conf_file, env=input_params.env)

        # override config with arguments (except null values)
        for key, value in input_params.dict().items():
            if value is not None:
                self.conf[key] = value

        # get metadata of the current run
        metadata = json.loads(
            self.dbutils.notebook.entry_point.getDbutils()
            .notebook()
            .getContext()
            .toJson()
        )
        # global run id
        self.conf["multitaskParentRunId"] = metadata["tags"].get(
            "multitaskParentRunId"
        )

    @staticmethod
    def _read_config(conf_file, env=None) -> Dict[str, Any]:
        config = yaml.safe_load(pathlib.Path(conf_file).read_text())
        if env:
            config = config["env"][env]
            config["env"] = env
        return config

    def _prepare_logger(self):
        from {{cookiecutter.package_name}} import logger
        return logger

    def _log_conf(self):
        self.logger.info(f"Launching job with configuration parameters: \n{yaml.dump(self.conf)}")

    @abstractmethod
    def launch(self):
        """
        Main method of the job.
        :return:
        """
        pass
