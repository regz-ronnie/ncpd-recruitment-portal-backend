#!/usr/bin/env python
"""
Test script to debug registration endpoint
"""
import requests
import json
import time

# Test data for registration with unique email
timestamp = int(time.time())
test_data = {
    "email": f"test{timestamp}@example.com",
    "first_name": "Test",
    "last_name": "User",
    "password": "TestPassword123!",
    "password_confirm": "TestPassword123!"
}

def test_registration():
    url = "http://127.0.0.1:8000/api/auth/register/"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    print("Testing registration endpoint...")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=test_data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
        elif response.status_code == 400:
            print("❌ Bad Request - Validation failed")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print("Could not parse error response as JSON")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error - Make sure the Django server is running")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_registration()
