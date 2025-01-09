#!/usr/bin/env python
import os
import json
import re
import redis
import logging

from flask import Flask, request, jsonify
from worker import celery
from handlers.normalization import normalize_city_name
from handlers.redis_utils import check_redis_connection
from celery_queue.tasks import process_weather_data

# Flask app setup
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

celery.conf.update(app.config)
redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, db=0, decode_responses=True)
check_redis_connection(redis_client)

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
