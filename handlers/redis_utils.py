import logging
import redis

def check_redis_connection(redis_client):
    """
    Check if Redis is accessible.
    """
    try:
        redis_client.ping()
        logging.info("Connected to Redis successfully")
    except redis.ConnectionError as e:
        logging.error(f"Redis connection failed: {e}")
        raise