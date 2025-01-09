import os
import json
import uuid
import redis
import requests
import logging

from worker import celery
from handlers.classification import classify_region
from handlers.get_api_key import get_api_key

API_KEY = os.getenv('API_KEY', '')
BASE_URL = os.getenv('BASE_URL', '')

redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, db=1, decode_responses=True)

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def process_weather_data(self, cities):
    """
    Fetch and process weather data for the given cities.
    """
    results = {}

    for city in cities:
        try:
            api_key = get_api_key()
            response = requests.get(
                f"{BASE_URL}?access_key={api_key}&query={city}"
            )
            if response.status_code != 200:
                results[city] = {"error": "City not found"}
                continue

            data = response.json()
            if "current" not in data or "location" not in data:
                results[city] = {"error": "Invalid data from API"}
                continue

            temp = data["current"].get("temperature")
            if temp is None or not (-50 <= temp <= 50):
                results[city] = {"error": "Invalid temperature data"}
                continue

            region = classify_region(city)
            results[city] = {
                "city": data["location"]["name"],
                "temperature": round(temp, 1),
                "description": data["current"]["weather_descriptions"][0],
                "region": region,
            }

        except requests.exceptions.RequestException as e:
            self.retry(exc=e)
            results[city] = {"error": str(e)}

    # Save results by region
    task_id = self.request.id
    grouped_results = {}
    for city, data in results.items():
        if "region" in data:
            region = data["region"]
            grouped_results.setdefault(region, []).append(data)

    for region, region_data in grouped_results.items():
        task_id = getattr(self.request, 'id', None) or str(uuid.uuid4())
        file_path = f"weather_data/{region}/"
        os.makedirs(f"weather_data/{region}", exist_ok=True)
        with open(f"{file_path}/task_{task_id}.json", "w") as f:
            json.dump(region_data, f, indent=2, ensure_ascii=False)

    logging.info(f"Saving results for task {task_id} to Redis: {results}")
    task_id = getattr(self.request, 'id', None) or str(uuid.uuid4())
    redis_client.set(task_id, json.dumps(results,  ensure_ascii=False))

    return results