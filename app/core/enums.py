# app/utils/statuses.py
from enum import StrEnum


class JobStatus(StrEnum):
    
    SAVED_ID = "saved_id"
    
    SCRAPING = "scraping"
    SCRAPED = "scraped"
    
    FORM_FILLING = "form_filling"
    FORM_FILLED = "form_filled"
    
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    
    APPLYING = "applying"
    APPLIED = "applied"

    SCRAPE_FAILED = "scrape_failed"
    ANALYZE_FAILED = "analyze_failed"
    APPLY_FAILED = "apply_failed"

    JOB_EXPIRED = "job_expired"
    REJECTED = "rejected"
    NEEDS_MANUAL_REVIEW = "needs_manual_review"


class APIStatus(StrEnum):
    DUPLICATE = "duplicate"
    JOB_STUB_CREATED = "job_stub_created"
    ERROR = "error"
    NOT_FOUND = "not_found"
    JOB_DETAILS_UPDATED = "job_details_updated"
    JOB_FORM_FIELD_CREATED = "job_form_field_created"
    CLAIMED = "claimed"


class APIError(StrEnum):
    INTEGRITY = "integrity"
    DB = "db"
    UNEXPECTED = "unexpected"


class ScrapeError(StrEnum):
    TIMEOUT = "timeout_waiting_for_selectors"
