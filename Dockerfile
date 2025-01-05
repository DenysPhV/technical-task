FROM python:3.10-alpine
LABEL authors="Denys_test"

ENV APP_HOME /app
WORKDIR $APP_HOME

COPY requirements.txt .

RUN \
   apk add --no-cache postgresql-libs && \
   apk add --no-cache --virtaul .build-deps gcc musl-dev postgresql-dev && \
   python3 -m pip install -r  requirements.txt --no-cache-dir && \
   apk --purge del .build-deps

COPY . .
ENTRYPOINT ["python"]
CMD ["api/main.py"]