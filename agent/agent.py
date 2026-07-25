import os
import time
import json
import platform
import logging
import requests
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration settings (environment variables with defaults)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api/providers/heartbeat/")
PROVIDER_ID = os.getenv("PROVIDER_ID", "provider-default-id")
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "10"))  # in seconds
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN", "")  # Optional JWT Token for authenticated association

def get_system_stats():
    """Gathers system resources stats."""
    try:
        stats = {
            "provider_id": PROVIDER_ID,
            "timestamp": time.time(),
            "cpu_usage_percent": psutil.cpu_percent(interval=1),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
            "memory_used_gb": round(psutil.virtual_memory().used / (1024 ** 3), 2),
            "memory_usage_percent": psutil.virtual_memory().percent,
            "disk_total_gb": round(psutil.disk_usage('/').total / (1024 ** 3), 2),
            "disk_used_gb": round(psutil.disk_usage('/').used / (1024 ** 3), 2),
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "os_name": platform.system(),
            "os_version": platform.release(),
        }
        return stats
    except Exception as e:
        logger.error(f"Error gathering system stats: {e}")
        return None

def send_heartbeat(stats):
    """Sends the gathered statistics to the backend server."""
    try:
        headers = {'Content-Type': 'application/json'}
        if PROVIDER_TOKEN:
            headers['Authorization'] = f'Bearer {PROVIDER_TOKEN}'
        response = requests.post(BACKEND_URL, data=json.dumps(stats), headers=headers, timeout=5)
        if response.status_code in [200, 201]:
            logger.info("Heartbeat sent successfully.")
        else:
            logger.warning(f"Failed to send heartbeat. Server returned status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error communicating with backend: {e}")

def main():
    logger.info(f"Starting provider monitoring agent for Provider: {PROVIDER_ID}")
    logger.info(f"Target backend URL: {BACKEND_URL}")
    
    while True:
        stats = get_system_stats()
        if stats:
            logger.info(f"Gathered Stats -> CPU: {stats['cpu_usage_percent']}%, Memory: {stats['memory_usage_percent']}%")
            send_heartbeat(stats)
        time.sleep(HEARTBEAT_INTERVAL)

if __name__ == "__main__":
    main()
