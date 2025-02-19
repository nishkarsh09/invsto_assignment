import requests
import json

def test_api_endpoints():
    """Test the API endpoints with the loaded data"""
    base_url = "http://localhost:8000"
    
    # Test GET /data endpoint
    response = requests.get(f"{base_url}/data")
    if response.status_code == 200:
        data = response.json()
        print(f"Successfully retrieved {len(data)} records")
        # Print first record as sample
        print("Sample record:", json.dumps(data[0], indent=2))
    else:
        print("Error getting data:", response.text)
    
    # Test POST /data endpoint with sample data
    sample_data = {
        "datetime": "2023-01-01T00:00:00",
        "open": 100.0,
        "high": 110.0,
        "low": 90.0,
        "close": 105.0,
        "volume": 1000
    }
    
    response = requests.post(f"{base_url}/data", json=sample_data)
    if response.status_code == 200:
        print("Successfully added sample record")
    else:
        print("Error adding data:", response.text)
    
    # Test strategy performance endpoint
    response = requests.get(f"{base_url}/strategy/performance")
    if response.status_code == 200:
        performance = response.json()
        print("\nStrategy Performance:")
        print(json.dumps(performance, indent=2))
    else:
        print("Error getting strategy performance:", response.text)

if __name__ == "__main__":
    test_api_endpoints() 