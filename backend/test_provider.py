import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api"

def run_tests():
    print("--- 1. Registering Provider User ---")
    username = f"provider_{int(time.time())}"
    reg_payload = {
        "username": username,
        "email": f"{username}@example.com",
        "password": "SecurePassword123!",
        "role": "provider"
    }
    
    reg_response = requests.post(f"{BASE_URL}/auth/register/", json=reg_payload)
    print(f"Registration Status: {reg_response.status_code}")
    reg_data = reg_response.json()
    print(json.dumps(reg_data, indent=2))
    
    if reg_response.status_code != 201:
        print("Registration failed.")
        return
        
    access_token = reg_data["access"]
    
    print("\n--- 2. Sending Heartbeat as Authenticated Provider ---")
    heartbeat_payload = {
        "provider_id": "test-machine-uuid-12345",
        "cpu_usage_percent": 15.4,
        "memory_total_gb": 16.0,
        "memory_used_gb": 4.2,
        "memory_usage_percent": 26.25,
        "disk_total_gb": 512.0,
        "disk_used_gb": 120.5,
        "disk_usage_percent": 23.53,
        "os_name": "Windows",
        "os_version": "11"
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    hb_response = requests.post(f"{BASE_URL}/providers/heartbeat/", json=heartbeat_payload, headers=headers)
    print(f"Heartbeat Status: {hb_response.status_code}")
    print(json.dumps(hb_response.json(), indent=2))
    
    print("\n--- 3. Listing Provider Machines ---")
    machines_response = requests.get(f"{BASE_URL}/providers/machines/")
    print(f"Machines List Status: {machines_response.status_code}")
    print(json.dumps(machines_response.json(), indent=2))

if __name__ == "__main__":
    run_tests()
