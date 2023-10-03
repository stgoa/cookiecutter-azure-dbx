FROM python:3.9 as base
WORKDIR /app
COPY . .
RUN python -m pip install --upgrade pip
RUN pip install poetry
# Install the project dependencies to bake the Cookiecutter template
RUN poetry install
# Bake the Cookiecutter template
RUN poetry run cookiecutter --no-input --overwrite-if-exists .
# Change the working directory to the new project
WORKDIR /app/MyProjectName
# Create and activate a virtual environment
RUN python -m venv venv
ENV PATH="/app/MyProjectName/venv/bin:$PATH"
RUN . venv/bin/activate
# Install the project dependencies
RUN poetry install --with dev,test
# Run the tests
RUN poetry run pytest
