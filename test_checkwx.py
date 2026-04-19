import requests

API_KEY = "a0288b8584804d0c95d2af0b8884d3b6"
ICAOS = ["VGZR", "VGEG", "VGSY", "VGJR"]

for icao in ICAOS:
    url = f"https://api.checkwx.com/metar/{icao}/decoded"
    headers = {"X-API-Key": API_KEY}
    print(f"\n--- {icao} ---")
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Content type: {type(resp.text)}")
        # Try to parse JSON
        try:
            data = resp.json()
            print(f"JSON type: {type(data)}")
            if isinstance(data, dict):
                print(f"Keys: {list(data.keys())}")
                if 'results' in data:
                    print(f"Results count: {len(data['results'])}")
                    if data['results']:
                        print(f"First result raw: {data['results'][0].get('raw', '')[:100]}")
            else:
                print(f"Data is not dict: {data}")
        except:
            print(f"Raw response: {resp.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")