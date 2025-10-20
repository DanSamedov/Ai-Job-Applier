import os
from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

response = client.models.generate_content(
    model='gemini-2.5-flash', contents='Why is the sky blue?'
)
print(response.text)

