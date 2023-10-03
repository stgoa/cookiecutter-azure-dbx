# {{cookiecutter.package_name}}

**{{cookiecutter.package_name}}** is a project that automates the deployment of blah blah, utilizing dbx.

Before you begin using this project, ensure that you have Python 3.9 and `pip` for package management installed on your system.

## Local environment setup

1. Install python

```bash
brew install python@3.9
```

2. Install poetry, a python packaging and dependency management.

```bash
brew install poetry
```

3. If you don't have JDK installed on your local machine, install it:

```bash
brew install openjdk@11
```

4. Install project locally (this will also install dev requirements):

```bash
# create a virtual env
python3.9 -m venv .env
# activate it (alternatively use poetry shell)
source .venv/bin/activate
# set external url
poetry config https-basic.$ARTIFACT_FEED $USERNAME_FEED $TOKEN_FEED
# install dependencies in isolated environment
poetry install --with dev,test
```

The environment variable `ARTIFACT_FEED` and `USERNAME_FEED` are `privatefeed` and `PASSWORD_FEED` is the Personal Access Token (PAT) created by the user.

The commands in the following sections can be ran with `poetry run <command>` or exactly as they are from inside a poetry environment activated with `poetry shell`.

5. Install pre-commit hooks (development)

```bash
pre-commit install
```

## Running unit tests

For unit testing, please use `pytest`:

```bash
pytest tests/unit --cov
```

Please check the directory `tests/unit` for more details on how to use unit tests.
In the `tests/unit/conftest.py` you'll also find useful testing primitives, such as local Spark instance with Delta support, local MLflow and DBUtils fixture.

## Running integration tests

There are two options for running integration tests:

- On an all-purpose cluster via `dbx execute`
- On a job cluster via `dbx launch`

For quicker startup of the job clusters we recommend using instance pools ([AWS](https://docs.databricks.com/clusters/instance-pools/index.html), [Azure](https://docs.microsoft.com/en-us/azure/databricks/clusters/instance-pools/), [GCP](https://docs.gcp.databricks.com/clusters/instance-pools/index.html)).

For an integration test on all-purpose cluster, use the following command:

```
dbx execute <workflow-name> --cluster-name=<name of all-purpose cluster>
```

To execute a task inside multitask job, use the following command:

```
dbx execute <workflow-name> \
    --cluster-name=<name of all-purpose cluster> \
    --job=<name of the job to test> \
    --task=<task-key-from-job-definition>
```

For a test on a job cluster, deploy the job assets and then launch a run from them:

```
dbx deploy <workflow-name> --assets-only
dbx launch <workflow-name>  --from-assets --trace
```

## Interactive execution and development on Databricks clusters

1. `dbx` expects that cluster for interactive execution supports `%pip` and `%conda` magic [commands](https://docs.databricks.com/libraries/notebooks-python-libraries.html).
2. Please configure your workflow (and tasks inside it) in `conf/deployment.yml` file.
3. To execute the code interactively, provide either `--cluster-id` or `--cluster-name`.

```bash
dbx execute <workflow-name> \
    --cluster-name="<some-cluster-name>"
```

Multiple users also can use the same cluster for development. Libraries will be isolated per each user execution context.

## Working with notebooks and Repos

To start working with your notebooks from a Repos, do the following steps:

1. Add your git provider token to your user settings in Databricks
2. Add your repository to Repos. This could be done via UI, or via CLI command below:

```bash
databricks repos create --url <your repo URL> --provider <your-provider>
```

This command will create your personal repository under `/Repos/<username>/{{cookiecutter.workflow_name}}`.

3. Use `git_source` in your job definition as described [here](https://dbx.readthedocs.io/en/latest/guides/python/devops/notebook/?h=git_source#using-git_source-to-specify-the-remote-source)

## CI/CD pipeline settings

Please set the following secrets or environment variables for your CI provider:

- `DATABRICKS_HOST`
- `DATABRICKS_TOKEN`
- `PIP_EXTRA_INDEX_URL`

## Testing and releasing via CI pipeline

- To trigger the CI pipeline, simply push your code to the repository. If CI provider is correctly set, it shall trigger the general testing pipeline
- To trigger the release pipeline, get the current version from the `{{cookiecutter.workflow_name}}/__init__.py` file and tag the current code version:

```
git tag -a v<your-project-version> -m "Release tag for version <your-project-version>"
git push origin --tags
```

## Sample Task

This project deploys an sample data computation task using `private-package==0.2.2` on Databricks.

The task reads and writes to an Azure DataLake Storage, the data is stored as Delta table on it and registered in a database on Databricks.

### Parameters

The task uses two main parameters. The first one is `--conf-file`, the configuration file to read, in this case corresponds to `sample_task_config.yml`. The second one is `--env`, the environment to use (dev, staging or prod), this variable is used to know what part of the config file to use. The meaning of each argument of the configuration file is detailed below.

- `env`: Specifies the environment to use (dev, staging, or prod). This parameter determines which subset of configurations from the file will be utilized.
- `experiment`: Defines the workspace directory for the MLflow experiment. It is dynamically generated based on the environment.
- `execution_date`: Specifies the execution date, set to "2023-09-01" if the environment is not 'prod'.
- `model_kwargs`:
    - `learning_rate`: Sets the learning rate. (Default: 0.1)
    - `max_iter`: Defines the maximum number of iterations in the optimization. (Default: 1000)
    - `tol`: Sets the tolerance level in the optimization. (Default: 0.0001)
- `database`: Name of the database (both for input and output). It will be created if not exists. Delta tables are registered in it.
- `table`: Name of the table with elasticity data
- `path`: Path where the cross-elasticity data is stored


### Cluster policy

The cluster policy limits the ability to configure clusters based on a set of rules. In this case, the policy `cluster-policy://Job Compute Data Lake` is used. It inherit the `Job Compute` policy family, adding the following configuration.

```json
  // spark config to establish conextion with the azure datalake
  "spark_conf.fs.azure.account.key.<datalake>.dfs.core.windows.net": {
    "type": "fixed",
    "value": "{{cookiecutter.datalake_token}}"
  },
  // environment variable created in runtime, used in init script
  "spark_env_vars.PIP_EXTRA_INDEX_URL": {
    "type": "fixed",
    "value": "{{cookiecutter.pypi_extra_index_url}}"
  },
  // to enable apache arrow, used in Spark to efficiently transfer data between
  // JVM and Python processes
  "spark_conf.spark.sql.execution.arrow.pyspark.enabled": {
    "type": "fixed",
    "value": "true"
  }
```
