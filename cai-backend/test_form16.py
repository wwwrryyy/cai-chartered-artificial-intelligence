import requests
import base64
import json

file_path = "/Users/shawnsc/Desktop/form_16.png"
with open(file_path, "rb") as f:
    files = {'files': ('form_16.png', f, 'image/png')}
    response = requests.post("http://localhost:8001/api/upload", files=files)
    
print("Status Code:", response.status_code)
print("Response:", json.dumps(response.json(), indent=2))
