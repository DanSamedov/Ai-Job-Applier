# app/services/analyze.py
from google import genai
from google.genai import types
from typing import Iterator, Dict, Any, List, Optional

from app.repositories.job_dao import JobDAO
from app.core.database import SessionLocal
from app.core.logger import setup_logger
from app.core.config import settings
from app.core.enums import JobStatus

class Analyze:
    def __init__(self, client):
        self.client = client


    def test(self):
        response = self.client.models.generate_content(
            model='gemini-2.5-flash', contents='What is 1+1'
        )
        print(response.text)


if __name__ == "__main__":
    logger = setup_logger(__name__)

    client = genai.Client(api_key=settings.gemini_api_key)
    analyzer = Analyze(client)

    dao = JobDAO(session=SessionLocal)
    job_field = dao.claim_job_for_processing(JobStatus.FORM_FIELDS_SCRAPED, JobStatus.ANALYZED)

    analyzer.test()
