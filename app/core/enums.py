# app/utils/statuses.py
from enum import StrEnum


class JobStatus(StrEnum):
    
    SAVED_ID = "saved_id"
    SAVING_ID_FAILED = "saving_id_failed"
    
    SCRAPING_DETAILS = "scraping_details"
    SCRAPED_DETAILS = "details_scraped"
    SCRAPING_DETAILS_FAILED = "scraping_details_failed"

    SCRAPING_FORM_FIELDS = "scraping_form_fields"
    FORM_FIELDS_SCRAPED= "form_fields_scraped"
    SCRAPING_FORM_FIELDS_FAILED = "scraping_form_fields_failed"

    ANALYZING_DETAILS = "analyzing_details"
    ANALYZED_DETAILS = "analyzed_details"
    ANALYZING_DETAILS_FAILED = "analyzing_details_failed"

    ANALYZING_FORM_FIELDS = "analyzing_form_fields"
    ANALYZED_FORM_FIELDS = "analyzed_form_fields"
    ANALYZING_FORM_FIELDS_FAILED = "analyzing_form_fields_failed"

    ANSWERING_FORM_FIELDS = "answering_form_fields"
    ANSWERED_FORM_FIELDS = "answered_form_fields"
    ANSWERING_FORM_FIELDS_FAILED = "answering_form_fields_failed"

    APPLYING = "applying"
    APPLIED = "applied"
    APPLYING_FAILED = "apply_failed"

    JOB_EXPIRED = "job_expired"
    REJECTED = "rejected"
    NEEDS_MANUAL_REVIEW = "needs_manual_review"


class APIStatus(StrEnum):
    DUPLICATE = "duplicate"
    JOB_STUB_CREATED = "job_stub_created"
    ERROR = "error"
    NOT_FOUND = "not_found"
    JOB_DETAILS_UPDATED = "job_details_updated"
    JOB_STATUS_UPDATED = "job_details_updated"
    JOB_FORM_FIELDS_CREATED = "job_form_field_created"
    CLAIMED = "claimed"


class APIError(StrEnum):
    INTEGRITY = "integrity"
    DB = "db"
    UNEXPECTED = "unexpected"


class ScrapeError(StrEnum):
    TIMEOUT = "timeout_waiting_for_selectors"


class FormFieldType(StrEnum):
    SKILL_INPUT = "skill_input"
    TEXT = "text"
    RADIO = "radio"
    NUMBER = "number"


class JobSource(StrEnum):
    DJINNI = "djinni"
    LINKED_IN = "linked_in"
