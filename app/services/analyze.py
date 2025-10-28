# app/services/analyze.py
from google import genai
from google.genai import types

from app.core.config import settings


client = genai.Client(api_key=settings.gemini_api_key)

response = client.models.generate_content(
    model='gemini-2.5-pro', contents='Why is the sky blue?'
)
print(response.text)
