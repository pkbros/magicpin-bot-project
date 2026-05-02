import os
import json
from urllib import request, error
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GROQ_API_KEY")
model = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

print(f"Testing with API key: {api_key[:5]}...{api_key[-5:]}")

url = "https://api.groq.com/openai/v1/chat/completions"
data = json.dumps({
    "model": model,
    "messages": [{"role": "user", "content": "Hello"}],
    "temperature": 0.2
}).encode("utf-8")

req = request.Request(
    url,
    data=data,
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
)

try:
    with request.urlopen(req) as response:
        print(f"Status: {response.status}")
        print(response.read().decode())
except error.HTTPError as e:
    print(f"HTTP Error: {e.code} {e.reason}")
    print(e.read().decode())
except Exception as e:
    print(f"Error: {e}")
