from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from app.core.enums import JobStatus, JobSource, FormFieldType, APIStatus, APIError


class JobStub(BaseModel):
    id: int
    external_id: int
    source: JobSource
    status: JobStatus
    found_at: datetime


class JobStubCreate(BaseModel):
    external_id: int
    source: JobSource = JobSource.DJINNI


class JobDetails(BaseModel):
    id: int
    title: str
    company: str
    description: str
    link: str
    scraped_at: Optional[datetime]


class JobDetailsCreate(BaseModel):
    external_id: int
    title: str
    company: str
    description: str
    link: str


class AnswerOption(BaseModel):
    text: str
    value: str


class JobFormField(BaseModel):
    id: int
    job_id: int
    external_field_id: str
    question: str
    answer_type: FormFieldType
    answer_options: Optional[List[AnswerOption]]
    answer: Optional[str]
    scraped_at: Optional[datetime]
    sent_at: Optional[datetime]


class JobFormFieldCreate(BaseModel):
    external_field_id: str
    question: str
    answer_type: FormFieldType
    answer_options: Optional[List[AnswerOption]]


class JobResponse(BaseModel):
    status: APIStatus
    external_id: Optional[int] = None
    id: Optional[int] = None
    error: Optional[APIError] = None
