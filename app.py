#!/usr/bin/env python
import os
import json
import re
import uuid

import redis
import logging
import requests

import celery.states as states

from flask import Flask, request, jsonify
from worker import celery
from handlers.get_api_key import get_api_key
from handlers.classification import classify_region
from handlers.normalization import normalize_city_name
# Flask app setup
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


celery.conf.update(app.config)
redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, db=1, decode_responses=True)

API_KEY = os.getenv('API_KEY', '')
BASE_URL = "https://api.weatherstack.com/current"

# TODO refactoring - bring to folder of celery-queue to task.py
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

try:
    redis_client.ping()
    logging.info("Connected to Redis successfully")
except redis.ConnectionError as e:
    logging.error(f"Redis connection failed: {e}")

@app.route('/', methods=['GET'])
def hello():
    return "Hello there!"

@app.route('/weather', methods=['POST'])
def get_weather():
    """
    Accept a list of cities and initiate asynchronous weather data processing.
    """
    data = request.get_json()
    cities = data.get('cities', [])
    if not cities or not all(isinstance(city, str) for city in cities):
        return jsonify({"error": "Invalid input. Please provide a list of city names."}), 400

    def validate_city_name(city):
        return re.match(r"^[a-zA-Zа-яА-ЯёЁ'\\s-]+$", city)

    # Normalize and clean city names
    normalized_cities = [normalize_city_name(city.strip()) for city in cities if validate_city_name(city)]
    task = process_weather_data.apply_async(args=[normalized_cities])

    return jsonify({"status": "completed", "task_id": task.id}), 202

@app.route('/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    task = process_weather_data.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {"status": "running"}
    elif task.state == 'SUCCESS':
        # Retrieve results from Redis
        result = redis_client.get(task_id)
        response = {"status": "completed", "result": json.loads(result)}
    elif task.state == 'FAILURE':
        response = {"status": "failed", "error": str(task.info)}
    else:
        response = {"status": task.state}
    return jsonify(response)

@app.route('/results/<region>', methods=['GET'])
def get_results_by_region(region):
    """
    Returns a list of cities and their data for the specified region.
    """
    file_path = f"weather_data/{region}/"
    if not os.path.exists(file_path):
        return jsonify({"error": "No data found for the specified region"}), 404

    grouped_results = {region: []}
    for file_name in os.listdir(file_path):
        try:
            with open(os.path.join(file_path, file_name), "r") as f:
                region_data = json.load(f)
                grouped_results[region].extend(region_data)
        except Exception as e:
            logging.error(f"Error reading file {file_name}: {e}")
            continue

    if not grouped_results[region]:
        return jsonify({"error": "No data found for the specified region"}), 404

    return jsonify({"status": "completed", "results": grouped_results})

if __name__ == '__main__':
    app.run(debug=True)
