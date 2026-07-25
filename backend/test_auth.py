import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/auth"

def run_tests():
    print("--- 1. Testing Registration ---")
    reg_payload = {
        "username": f"testuser_{int(time.time())}",
        "email": f"testuser_{int(time.time())}@example.com",
        "password": "SecurePassword123!",
        "role": "renter"
    }
    
    reg_response = requests.post(f"{BASE_URL}/register/", json=reg_payload)
    print(f"Registration Status Code: {reg_response.status_code}")
    reg_data = reg_response.json()
    print(json.dumps(reg_data, indent=2))
    
    if reg_response.status_code != 201:
        print("Registration failed.")
        return

    # Extract credentials
    username = reg_payload["username"]
    password = reg_payload["password"]
    access_token = reg_data["access"]
    refresh_token = reg_data["refresh"]

    print("\n--- 2. Testing Login ---")
    login_payload = {
        "username": username,
        "password": password
    }
    login_response = requests.post(f"{BASE_URL}/login/", json=login_payload)
    print(f"Login Status Code: {login_response.status_code}")
    login_data = login_response.json()
    print(json.dumps(login_data, indent=2))

    if login_response.status_code != 200:
        print("Login failed.")
        return
        
    access_token = login_data["access"]
    refresh_token = login_data["refresh"]

    print("\n--- 3. Testing Get Current User Profile (/me/) ---")
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    me_response = requests.get(f"{BASE_URL}/me/", headers=headers)
    print(f"Get Profile Status Code: {me_response.status_code}")
    print(json.dumps(me_response.json(), indent=2))

    print("\n--- 4. Testing Token Refresh ---")
    refresh_payload = {
        "refresh": refresh_token
    }
    refresh_response = requests.post(f"{BASE_URL}/refresh/", json=refresh_payload)
    print(f"Refresh Status Code: {refresh_response.status_code}")
    print(json.dumps(refresh_response.json(), indent=2))

if __name__ == "__main__":
    # Wait a second for Django file reload
    time.sleep(1)
    run_tests()
