FROM python:3.9-slim

ARG MODEL_VERSION=master

# Root directory in the container
WORKDIR /eucalc

# Install python dependencies
RUN pip install --upgrade setuptools
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy all source files for production
# COPY ./knime2python/scripts ./knime2python/scripts
# COPY ./knime2python/src ./knime2python/src

COPY ./knime2python ./knime2python
COPY ./model ./model
COPY ./_database ./_database
COPY ./config ./config
# Set environment variable for python code to find sources
ENV PYTHONPATH /eucalc

# API interface port, to match with API config
EXPOSE 5000

# Run the API

# Entrypoint for Green Unicorn, sets timeout to 500 to allow the model time to build.
# These parameters are not meant to be changed at run time.
ENTRYPOINT ["gunicorn", "knime2python.src.api.app:build_app(\"knime2python/config/config_docker_eu.yml\")", "--timeout", "500", "--bind", "0.0.0.0:5000", "--backlog", "0"]

# This sets the default to 1 worker, works with 4GB RAM
# To override, run `docker run -p 5000:5000 <image> -w 2`
CMD ["--workers", "1"]

# For testing purposes: run the app with Flask
# CMD ["python", "/eucalc/scripts/eucalc-app.py", "-c", "config/config_docker.yml"]
