# Cookiecutter-Azure-DBX

[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-390/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Cookiecutter-Azure-DBX is a Python project template designed for seamless development of PySpark Databricks workflows. Supercharge your projects with automated continuous integration in Azure and effortless Databricks workflow deployment using DBX.

## Features

- [DBX](https://dbx.readthedocs.io/en/latest/) automatic deployment from within the CI/CD pipeline.
- [Poetry](https://python-poetry.org/) package manager.
- Code formatting with [black](https://github.com/psf/black), [autopep8](https://github.com/hhatto/autopep8), [isort](https://pycqa.github.io/isort/), and [docformatter](https://github.com/PyCQA/docformatter), along with linting using [pylint](https://pylint.org/), [bandit](https://github.com/PyCQA/bandit), [flake8](https://flake8.pycqa.org/en/latest/), and [mypy](https://mypy.readthedocs.io/en/stable/).
- Environment variables loaded using [python-dotenv](https://github.com/theskumar/python-dotenv) from a `.env` file.
- Logger configured using [structlog](https://www.structlog.org/en/stable/) to save in JSON format and track function execution.
- [Pydantic](https://pydantic-docs.helpmanual.io/) integration in settings as a class that inherits from `pydantic.BaseSettings`.
- [Yglu](https://yglu.io/) configuration files for DBX.

## The CICD Azure Pipeline File


Simple continuous integration using [Docker Tasks](https://docs.microsoft.com/en-us/azure/devops/pipelines/tasks/build/docker?view=azure-devops) to test and [DBX](https://dbx.readthedocs.io/en/latest/) to deploy the project.

### OnDevPullRequestJob

This job is designed to perform tasks related to features pull requests. Below are the steps performed in this job:

1. **Remove Docker Unused Data:**
   - Description: Prune Docker resources and volumes to ensure a clean environment.
   - Script:
     ```yaml
     script: docker system prune -af --volumes
     ```
   - DisplayName: Remove docker unused data

2. **Build Docker Image:**
   - Description: Build a Docker image with the specified build arguments.
   - Script:
     ```yaml
     script: |
       DOCKER_BUILDKIT=1 docker build \
       --build-arg DATABRICKS_HOST=$(DATABRICKS-HOST) \
       --build-arg DATABRICKS_TOKEN=$(DATABRICKS-TOKEN) \
       --build-arg ARTIFACT_FEED=$(ARTIFACT-FEED) \
       --build-arg USERNAME_FEED=$(USERNAME-FEED) \
       --build-arg TOKEN_FEED=$(TOKEN-FEED) \
       -t {{cookiecutter.workflow_name}} .
     ```
   - DisplayName: Build image

3.  **Run Unit Tests:**
   - Description: Execute unit tests using pytest.
   - Script:
     ```yaml
     script: |
       docker run --rm -t {{cookiecutter.workflow_name}} poetry run \
       pytest tests/unit -s -vvv
     ```
   - DisplayName: Run unit tests

### OnMainPullRequestJob

This job is designed to perform tasks related to development pull requests with integration tests included. Below are the steps performed in this job:

1. **Remove Docker Unused Data:**
   - Description: Prune Docker resources and volumes to ensure a clean environment.
   - Script:
     ```yaml
     script: docker system prune -af --volumes
     ```
   - DisplayName: Remove docker unused data

2. **Build Docker Image:**
   - Description: Build a Docker image with the specified build arguments.
   - Script:
     ```yaml
     script: |
       DOCKER_BUILDKIT=1 docker build \
       --build-arg DATABRICKS_HOST=$(DATABRICKS-HOST) \
       --build-arg DATABRICKS_TOKEN=$(DATABRICKS-TOKEN) \
       --build-arg ARTIFACT_FEED=$(ARTIFACT-FEED) \
       --build-arg USERNAME_FEED=$(USERNAME-FEED) \
       --build-arg TOKEN_FEED=$(TOKEN-FEED) \
       -t {{cookiecutter.workflow_name}} .
     ```
   - DisplayName: Build image

3. **Copy Init Script to DBFS:**
   - Description: Copy an initialization script to Databricks File System (DBFS).
   - Script:
     ```yaml
     script: |
       docker run --rm -t {{cookiecutter.workflow_name}} poetry run \
       dbfs cp resources/init_script.sh dbfs:/Shared/init_scripts/{{cookiecutter.package_name}}/staging_init_script.sh --overwrite
     ```
   - DisplayName: Copy init script to DBFS

4. **Run Unit Tests:**
   - Description: Execute unit tests using pytest.
   - Script:
     ```yaml
     script: |
       docker run --rm -t {{cookiecutter.workflow_name}} poetry run \
       pytest tests/unit -s -vvv
     ```
   - DisplayName: Run unit tests

5. **Deploy the Job:**
   - Description: Deploy the job to the staging environment using `dbx`.
   - Script:
     ```yaml
     script: |
       docker run --rm -t {{cookiecutter.workflow_name}} poetry run \
       dbx deploy staging-{{cookiecutter.workflow_name}} --environment staging
     ```
   - DisplayName: Deploy the job

6. **Launch Workflow:**
   - Description: Launch the workflow in the staging environment using `dbx`.
   - Script:
     ```yaml
     script: |
       docker run --rm -t {{cookiecutter.workflow_name}} poetry run \
       dbx launch staging-{{cookiecutter.workflow_name}} --environment staging --trace
     ```
   - DisplayName: Launch workflow

### OnReleaseJob

This job is triggered when a pull request is created from the release branch to the main branch. It handles tasks related to releasing new productive versions. Here are the steps performed in this job:

1. **Remove Docker Unused Data:**
   - Description: Prune Docker resources and volumes to ensure a clean environment.
   - Script:
     ```yaml
     script: docker system prune -af --volumes
     ```
   - DisplayName: Remove docker unused data

2. **Build Docker Image:**
   - Description: Build a Docker image with the specified build arguments.
   - Script:
     ```yaml
     script: |
       DOCKER_BUILDKIT=1 docker build \
       --build-arg DATABRICKS_HOST=$(DATABRICKS-HOST) \
       --build-arg DATABRICKS_TOKEN=$(DATABRICKS-TOKEN) \
       --build-arg ARTIFACT_FEED=$(ARTIFACT-FEED) \
       --build-arg USERNAME_FEED=$(USERNAME-FEED) \
       --build-arg TOKEN_FEED=$(TOKEN-FEED) \
       -t {{cookiecutter.workflow_name}} .
     ```
   - DisplayName: Build image

3. **Copy Init Script to DBFS:**
   - Description: Copy an initialization script to Databricks File System (DBFS).
   - Script:
     ```yaml
     script: |
       docker run --rm -t {{cookiecutter.workflow_name}} poetry run \
       dbfs cp resources/init_script.sh dbfs:/Shared/init_scripts/{{cookiecutter.package_name}}/prod_init_script.sh --overwrite
     ```
   - DisplayName: Copy init script to DBFS

4. **Run Unit Tests:**
   - Description: Execute unit tests using pytest.
   - Script:
     ```yaml
     script: |
       docker run --rm -t {{cookiecutter.workflow_name}} poetry run \
       pytest tests/unit -s -vvv
     ```
   - DisplayName: Run unit tests

5. **Deploy the Job:**
   - Description: Deploy the job to the production environment using `dbx`.
   - Script:
     ```yaml
     script: |
       docker run --rm -t {{cookiecutter.workflow_name}} poetry run \
       dbx deploy prod-{{cookiecutter.workflow_name}} --environment prod
     ```
   - DisplayName: Deploy the job



## Pydantic Settings

Project settings are controlled by Pydantic and can be found in `my_package.settings.py`. If you need to set an environment variable, you should edit the `Settings` class within `my_package.settings`. For example, suppose you need to add a connection string for a database system as an environment variable. In that case, you can do the following:

```python
# Other imports are here but not included in this example

from pydantic import SecretStr

class Settings(BaseSettings):
    """Project settings variables."""

    PACKAGE_PATH = Path(__file__).parent
    """Package path (Python files)."""

    PROJECT_PATH = PACKAGE_PATH.parent
    """Project path (all files)."""

    LOG_PATH: Optional[Path]
    """Path to the log file, only applicable if ``LOG_DESTINATION=FILE``."""

    LOG_FORMAT: LogFormatter = LogFormatter.COLOR.value
    """Log style."""

    LOG_LEVEL: LogLevel = LogLevel.INFO.value
    """Log level from the ``logging`` module."""

    LOG_DESTINATION: LogDest = LogDest.CONSOLE.value
    """Destination for logs."""

    CONNECTION_STRING: SecretStr  # This is a new mandatory environment variable

    class Config:
        """Inner configuration."""

        env_prefix = "MY_PACKAGE_"  # All environment variables with this prefix
        use_enum_values = True
```

You have three options to set the value for `CONNECTION_STRING`:

1. **Inside the Class Definition (Not Recommended for Passwords):** You can directly write the value inside the `Settings` class definition. However, this approach is not recommended for sensitive information like passwords.

2. **Using the `export` Command (Unix-like Systems) or `set` (Windows):** You can use the `export` command on Unix-like systems or `set` on Windows to set the value of the `CONNECTION_STRING` environment variable.

3. **Using a Configuration File (Recommended):** The easiest and recommended way is to write the `CONNECTION_STRING` in the configuration file named `.env`, located at the root of the project. Environment variables should be prefixed with `MY_PACKAGE_`, which is the name of the package in uppercase. Below is an example of an `.env` file with a simple PostgreSQL connection string:

```env
# .env file

MY_PACKAGE_CONNECTION_STRING=postgresql://foo:bar@localhost:5432/mydatabase
```

The project settings are in the top level `__init__`, to use it you have to import `SETTINGS` object

```python
from sqlalchemy import create_engine
from my_package import SETTINGS # Here SETTINGS is an instance of `my_package.settings.Settings`

engine = create_engine(SETTINGS.CONNECTION_STRING.get_secret_value()) # We declared the connection as SecretStr!
```

In this example, we use SQLAlchemy to create a database engine using the `CONNECTION_STRING` retrieved from the `SETTINGS` object. Note that we access `CONNECTION_STRING` as a secret value, as it's declared using `SecretStr` in the `Settings` class.

## Logging

A comprehensive logger is configured using `structlog`. You can control the logger's behavior through attributes in the settings class:

- `LOG_FORMAT`: This attribute can have two possible values, `JSON` or `COLOR` (the latter requires [colorama](https://github.com/tartley/colorama)). `JSON` provides structured JSON-format logs, while `COLOR` adds colorization for console output.

- `LOG_DESTINATION`: You can set this attribute to either `CONSOLE` or `FILE`. If you choose `FILE`, you must also specify the `LOG_PATH` attribute, which indicates the file where logs will be saved.

- `LOG_LEVEL`: This attribute sets the logging level for the logger, following the same levels as the [logging](https://docs.python.org/3/library/logging.html) module. The available levels include:
  - `logger.debug`: For debug-level messages.
  - `logger.info`: For informational messages.
  - `logger.warning`: For warning messages.
  - `logger.error`: For error messages.
  - `logger.critical`: For critical messages.

Here's an example `.env` file that sets the logger configuration:

```env
# .env file

MY_PACKAGE_LOG_LEVEL=20
MY_PACKAGE_LOG_DESTINATION=CONSOLE
MY_PACKAGE_LOG_FORMAT=JSON
```

The logger also accepts any additional ``kwarg`` arguments, allowing you to add more information, such as printing to the console.

```python

from my_package import logger

logger.info("This is an exmaple log", example_kwargs = "this is an example kwarg", other_example_kwargs = "this is other example kwarg")

>>> 2022-03-29T18:40:54.646488Z [info     ] This is an exmaple log         [pymooslotting] example_kwargs=this is an example kwarg other_example_kwargs=this is other example kwarg
```

## Custom Exceptions

In the `my_package.exc` module, you'll find a custom exception class that simplifies error message creation by allowing classes that inherit from it to render message variables inside the error message. Here's an example:

```python
# my_package.exc.py

class ExampleError(ErrorMixin, NameError):
    """Raise this when a table name has not been found."""

    msg_template = "This is an example class error, every `{variable}` inside the brackets will be part of the instantiation of the class and will be rendered in this message."
```

In this example, the ExampleError class inherits from ``ErrorMixin`` and ``NameError``. It provides a ``msg_template`` attribute where you can define a message template with placeholders like ``{variable}``. When you raise this exception and pass values for these placeholders as keyword arguments, they will be rendered in the error message.


## Acknowledgments

Special thanks to:
- [Andres Sandoval](https://github.com/andresliszt) for their work on the original project [cookiecutter-azure-poetry](https://github.com/andresliszt/cookiecutter-azure-poetry), which served as the inspiration and foundation for this project.
- [Diego Garrido](https://github.com/dgarridoa) for their valuable work on the project [dbx-demand-forecast](https://github.com/dgarridoa/dbx-demand-forecast). Diego's project has been a source of inspiration and learning in the field of demand forecasting with Databricks.

We are grateful for their valuable contributions and the open-source community's spirit of collaboration.


## TODO

- Write a better readme.
- Write a better TODO.
