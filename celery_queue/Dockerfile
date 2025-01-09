# Base Image
FROM python:3.9-slim

# Settind celere broker which is redis (default config)
ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0
ENV C_FORCE_ROOT true
ENV HOST 0.0.0.0
ENV PORT 5000
ENV DEBUG true

# Copying everything to the container folder
COPY . /app
WORKDIR /app

# Removing pywin32 from requirements.txt (more reliable approach)
RUN grep -v "pywin32" requirements.txt > fixed-requirements.txt && mv fixed-requirements.txt requirements.txt

# Installing all the dependencies in the container
RUN pip install -U setuptools pip
# Installing Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Exposing the app by port: 5000
EXPOSE 5000

RUN pip install gunicorn
# Startup command for this app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "app:app"]