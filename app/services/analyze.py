# app/services/analyze.py
from google import genai
from google.genai import types

from app.core.config import settings


class Analyze:
    def __init__(self, client):
        self.client = client


    def test(self):
        response = self.client.models.generate_content(
            model='gemini-2.5-flash', contents='What is 1+1'
        )
        print(response.text)


if __name__ == "__main__":
    client = genai.Client(api_key=settings.gemini_api_key)

    analyzer = Analyze(client)
    analyzer.test()