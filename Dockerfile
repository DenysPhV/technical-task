# Base Image
FROM python:3.9-slim

# Setting the broker for celery
ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0
ENV C_FORCE_ROOT true
# Moving every files to the container
COPY . /queue
WORKDIR /queue

# Removing pywin32 from requirements.txt (more reliable approach)
RUN grep -v "pywin32" requirements.txt > fixed-requirements.txt && mv fixed-requirements.txt requirements.txt

# Installing the dependencies
RUN pip install -U setuptools pip
RUN cat requirements.txt

RUN pip install --no-cache-dir -r requirements.txt
