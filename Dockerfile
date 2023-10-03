FROM python:3.9 as base
WORKDIR /app
COPY . .
RUN python -m pip install --upgrade pip
# Get JDK since we need it in the template
RUN apt-get update
RUN apt-get -y install openjdk-17-jdk
RUN pip install poetry
# Install the project dependencies to bake the Cookiecutter template
RUN poetry install --with dev,test
# Run the tests of the project
RUN poetry run pytest tests -s -vvv
# Bake the Cookiecutter template
RUN poetry run cookiecutter --no-input --overwrite-if-exists .
# Change the working directory to the new project
WORKDIR /app/MyProjectName
# Create and activate a virtual environment
RUN python -m venv venv
ENV PATH="/app/MyProjectName/venv/bin:$PATH"
RUN . venv/bin/activate
# Install the new project dependencies
RUN poetry install --with dev,test
# Run the new project tests
RUN poetry run pytest tests/unit -s -vvv
