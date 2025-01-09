# technical-task
- start envernoment on Win   ```.venv\Scripts\activate```
- by Linux ```source .venv/bin/activate```

### run docker
```
docker-compose build 
docker-compose up -d redis
docker-compose down
```

### start app 
```python app.py```

# Functionality:
### POST /weather 
- [x] Accepts the list of cities in the JSON request.
- [x] Normalizes city names.
- [x] Initializes an asynchronous task via Celery.
- [x] Returns task_id and results at once.

### GET /tasks/<task_id>
- [x] Checks the status of the job (running, completed, failed).
- [x] Returns a result from Redis if the task is completed.

### GET /results/<region>
- [x] Returns a list of cities and their data for a given region.
- [x] Reads results from files weather_data/<region>/.

### Обробка API-відповідей
- [x] Processing logic takes into account API errors.
- [x] Invalid data is filtered (temperature, no keys).
- [x] Results are grouped by region.

### Вимоги
- [x] API limits and errors factored through Celery with option max_retries.
- [x] Support for cities in multiple languages with name fixes.
- [x] Saving results to Redis and the file system.