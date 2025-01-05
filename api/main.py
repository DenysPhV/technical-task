#!/usr/bin/env python
import os
import json
import redis
import dotenv
import requests

from flask import Flask, request, jsonify
from celery import Celery

#Flask app setup
app = Flask(__name__)

# Celery configuration
app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL', "redis://localhost:6379/0")
app.config['CELERY_RESULT_BACKEND'] = os.getenv('CELERY_RESULT_BACKEND', "redis://localhost:6379/0")

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Redis client for task tracking
redis_client = redis.StrictRedis(host='localhost', port=6379, db=1, decode_responses=True)

API_KEY = os.getenv('API_KEY')
BASE_URL = os.getenv('BASE_URL')

# Helper function to classify regions
def classify_region(city):
    region_mapping = {
        "Kyiv": "Europe",
        "London": "Europe",
        "New York": "America",
        "Tokyo": "Asia"
    }
    return region_mapping.get(city, "Unknown")

@celery.task(bind=True)
def process_weather_data(self, cities):
    """
    Fetch and process weather data for given cities.
    :param self:
    :param cities:
    :return:
    """
    results = {}
    for city in cities:
        # Simulate API request (replace with real API call later)
        try:
            # Fetch data from OpenWeatherMap API
            response = requests.get(BASE_URL, params={"q": city, "key": API_KEY, "units": "metric"})
            if response.status_code == 200:
                data = response.json()
                weather_data = {
                    "city": city,
                    "temperature": data["main"]["temp"],
                    "description": data["weather"][0]["description"],
                    "region": classify_region(city)
                }
                results[city] = weather_data
            elif response.status_code == 404:
                results[city] = {"error": "City not found"}
            else:
                results[city] = {"error": f"API error: {response.status_code}"}

        except Exception as e:
            results[city] = {"error": str(e)}

    # Save results to Redis for simplicity
    task_id = self.request.id
    redis_client.set(task_id, json.dumps(results))
    return results

@app.route('/')
def test_start():
  return 'Hello, World I am FLask!'

@app.route('/weather', methods=['POST'])
def get_weather():
    """
    Accept a list of cities and initiate asynchronous weather data processing.
    """
    data = request.get_json()
    cities = data.get['cities', []]

    if not cities:
        return jsonify({"error": "Cities list is required"}), 400

    # Start the Celery task
    task = process_weather_data.apply_async(args=[cities])
    return jsonify({"task_id": task.id}), 202

@app.route('/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    Check the status of the given task.
    :param task_id:
    :return:
    """
    task = process_weather_data.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {"status": "running"}
    elif task.state == 'SUCCESS':
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
    :param region:
    :return:
    """
    grouped_results = {region: []}
    for key in redis_client.keys(f"{region}*"):
        task_results = json.loads(redis_client.get(key))
        for city, data in task_results.items():
            if isinstance(data, dict) and data.get('region') == region:
                grouped_results[region].append({
                    "city": city,
                    "temperature": data.get("temperature"),
                    "description": data.get("description")
                })


    if not grouped_results[region]:
        return jsonify({"error": "No data found for the specified region"}), 404

    return jsonify(grouped_results)

if __name__ == '__main__':
    app.run(debug=True)


