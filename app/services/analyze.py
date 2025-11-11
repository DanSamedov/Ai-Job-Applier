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

    
    def analyze_cv(self, cv):
        pass


    def analyze_job_details(self, job_details):
        if job_details:
            print(f"company name: {job_details.company}")
            print(f"job title: {job_details.title}")
            print(f"job description: {job_details.description}")
        else:
            print("job_details is not found")

    
    def analyze_job_form_fields(self, job_form_fields):
        for form_filed in job_form_fields:
            print(f"question: {form_filed.question}")
            print(f"answer_type: {form_filed.answer_type}")
            print(f"answer_options: {form_filed.answer_options}")


    def answer_job_form_fields(self, job_form_fields):
        pass


if __name__ == "__main__":
    logger = setup_logger(__name__)

    client = genai.Client(api_key=settings.gemini_api_key)
    analyzer = Analyze(client)

    dao = JobDAO(session=SessionLocal)

    # job = dao.claim_job_for_processing(JobStatus.FORM_FIELDS_SCRAPED, JobStatus.ANALYZING_DETAILS)
    job_details = dao.get_job_details(1)
    analyzer.analyze_job_details(job_details)

    # job = dao.claim_job_for_processing(JobStatus.ANALYZED_DETAILS, JobStatus.ANALYZING_FORM_FIELDS)
    # job_form_fields = dao.get_job_form_fields(38)
    # analyzer.analyze_job_form_fields(job_form_fields)

    # job = dao.claim_job_for_processing(JobStatus.ANALYZED_FORM_FIELDS, JobStatus.ANSWERING_FORM_FIELDS)
    # job_details = dao.get_job_details(job["id"])
    # analyzer.answer_job_form_fields(job_details)
