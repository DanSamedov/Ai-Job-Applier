# app/services/analyze.py
from google import genai
from google.genai import types

from app.config import settings


load_dotenv(settings.gemini_api_key)

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

response = client.models.generate_content(
    model='gemini-2.5-pro', contents='Why is the sky blue?'
)
print(response.text)
