FROM {{cookiecutter.python_docker_image}} as base
ARG DATABRICKS_HOST
ARG DATABRICKS_TOKEN
ENV DATABRICKS_HOST ${DATABRICKS_HOST}
ENV DATABRICKS_TOKEN ${DATABRICKS_TOKEN}
ARG ARTIFACT_FEED
ARG USERNAME_FEED
ARG TOKEN_FEED
WORKDIR /app
COPY . .
RUN python -m pip install --upgrade pip
RUN pip install poetry
RUN apt-get update
RUN apt-get -y install openjdk-17-jdk
RUN poetry config http-basic.${ARTIFACT_FEED} ${USERNAME_FEED} ${TOKEN_FEED}
RUN poetry install --with dev,test
# generate the DBX configuration files using yglu
RUN pip install yglu
RUN yglu conf/tasks/gen-sample_task_config.yml > conf/tasks/sample_task_config.yml
RUN yglu conf/gen-deployment.yml > conf/deployment.yml
