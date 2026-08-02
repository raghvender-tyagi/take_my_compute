import requests

# Set your cloud URL here
URL = "https://takemycompute-backend.onrender.com/api/auth/register/"

print("Creating a new cloud user...")

data = {
    "username": "admin",
    "password": "supersecretpassword",
    "email": "admin@example.com",
    "role": "both"
}

try:
    response = requests.post(URL, json=data)
    if response.status_code == 201:
        print("\n[SUCCESS] User created.")
        print(f"Username: {data['username']}")
        print(f"Password: {data['password']}")
        print("\n[KEY] YOUR CLOUD JWT ACCESS TOKEN IS:")
        print("-" * 50)
        print(response.json()['access'])
        print("-" * 50)
        print("\nPaste this token in your local gui_agent.py to connect to the cloud!")
    else:
        print(f"[FAILED] Failed to create user: {response.status_code}")
        print(response.json())
except Exception as e:
    print(f"[ERROR] Error connecting to cloud: {e}")
