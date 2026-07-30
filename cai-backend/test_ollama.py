import requests

try:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "gemma2:2b",
            "prompt": "Hello",
            "stream": False
        },
        timeout=10
    )
    print("OLLAMA OK:", response.json().get("response", ""))
except Exception as e:
    print("OLLAMA ERROR:", e)
