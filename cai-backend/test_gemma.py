import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMMA_API_KEY")
client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model=os.getenv("GEMMA_MODEL", "gemma-4"),
        contents="Hello, this is a test.",
    )
    print("TEXT OK:", response.text)
except Exception as e:
    print("TEXT ERROR:", e)

try:
    from PIL import Image
    img = Image.new('RGB', (100, 100))
    response = client.models.generate_content(
        model=os.getenv("GEMMA_MODEL", "gemma-4"),
        contents=["What is in this image?", img],
    )
    print("IMAGE OK:", response.text)
except Exception as e:
    print("IMAGE ERROR:", e)
