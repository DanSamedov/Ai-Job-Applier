# app/services/analyze.py
from google import genai
from google.genai import types
from dataclasses import dataclass
from typing import Dict, Any, List
import json

from app.core.logger import setup_logger
from app.core.config import settings

logger = setup_logger(__name__)

@dataclass
class FormAnswers:
    answers_by_field_id: Dict[str, str]
    raw: Dict[str, Any]


class CVProvider:
    def get_cv_text(self, path: str) -> str:
        raise NotImplementedError


class PromptFactory:
    def build_form_answer_prompt(self, cv_text: str, job_details: Any, form_fields: List[Any]) -> str:
        raise NotImplementedError


class GenAIClient:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.logger = logger


    def generate_json(self, prompt: str, model: str = settings.gemini_model) -> Dict[str, Any]:
        chosen_model = model
        resp = self.client.models.generate_content(
            model=chosen_model,
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["TEXT"]),
        )
        try:
            return json.loads(resp.text)
        except Exception:
            self.logger.warning("Model output not valid JSON; returning raw text.")
            return {"raw_text": resp.text}


class AnalysisEngine:
    def __init__(self, prompt_factory: PromptFactory, model_client: GenAIClient):
        self.prompt_factory = prompt_factory
        self.model_client = model_client
        self.logger = logger


    def answer_form_fields(self, job_details: Any, form_fields: List[Any], cv_text: str) -> FormAnswers:
        prompt = self.prompt_factory.build_form_answer_prompt(cv_text, job_details, form_fields)
        raw = self.model_client.generate_json(prompt)
        return self._parse_form_output(raw)


    def _parse_form_output(self, raw: Dict[str, Any]) -> FormAnswers:
        raise NotImplementedError
