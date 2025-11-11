# tests/integration/test_job_dao.py
import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.models.job import JobStub, JobDetails, JobFormField
from app.core.enums import JobStatus, APIStatus, FormFieldType


def test_save_new_job_stub(job_dao, db_session):
    job_data = {"external_id": 1}

    result = job_dao.save_job_stub(job_data=job_data)
    assert result["status"] == "job_stub_created"
    assert result["external_id"] == 1
    assert "id" in result

    count = db_session.query(JobStub).count()
    assert count == 1


def test_duplicate_job_stub(job_dao, db_session):
    job_data = {"external_id": 1}
    
    job_dao.save_job_stub(job_data=job_data)
    assert db_session.query(JobStub).count() == 1

    result = job_dao.save_job_stub(job_data=job_data)
    assert result["status"] == "duplicate"
    assert result["external_id"] == 1
    assert db_session.query(JobStub).count() == 1


def test_save_job_details(job_dao, db_session):
    job_details = {
        "external_id": 1,
        "title": "test_title",
        "company": "test_company",
        "description": "test_description",
        "link": "test_link",
        "status": "details_scraped"
    }

    save_job = job_dao.save_job_stub(job_data={"external_id": 1})
    assert db_session.query(JobStub).count() == 1

    result = job_dao.save_job_details(job_details)
    assert db_session.query(JobStub).count() == 1
    assert result["status"] == "job_details_updated"
    assert result["external_id"] == 1
    assert result["id"] == save_job["id"]

    assert db_session.query(JobDetails).count() == 1

    job = db_session.query(JobStub).filter_by(external_id=job_details["external_id"]).first()
    details = job.details
    assert details.title == "test_title"
    assert details.company == "test_company"
    assert details.description == "test_description"
    assert details.link == "test_link"
    assert job.status == "details_scraped"

    assert details.scraped_at is not None


def test_job_details_not_found(job_dao, db_session):
    job_details = {
        "external_id": 1,
        "title": "test_title",
        "company": "test_company",
        "description": "test_description",
        "link": "test_link",
        "status": "scraped"
    }

    assert db_session.query(JobStub).count() == 0

    result = job_dao.save_job_details(job_details)
    assert result["status"] == "not_found"
    assert result["external_id"] == 1
    assert db_session.query(JobStub).count() == 0


def test_claim_job_stub(job_dao, db_session):
    save_job = job_dao.save_job_stub(job_data={"external_id": 1})
    assert db_session.query(JobStub).count() == 1

    result = job_dao.claim_job_for_processing(
        current_status=JobStatus.SAVED_ID, 
        new_status=JobStatus.SCRAPED_DETAILS
    )
    assert result["status"] == APIStatus.CLAIMED
    assert result["external_id"] == 1
    assert result["id"] == save_job["id"]

    job = db_session.query(JobStub).filter_by(external_id=1).first()
    assert job is not None
    assert job.status == "details_scraped"


def test_job_stub_not_found(job_dao, db_session):
    result = job_dao.claim_job_for_processing(
        current_status=JobStatus.SAVED_ID, 
        new_status=JobStatus.SCRAPED_DETAILS
    )
    assert db_session.query(JobStub).count() == 0
    assert result["status"] == APIStatus.NOT_FOUND
    assert result["external_id"] == None


def test_claim_job_skips_wrong_status(job_dao, db_session):
    job_dao.save_job_stub(job_data={"external_id": 1})
    
    job = db_session.query(JobStub).first()
    job.status = JobStatus.SCRAPED_DETAILS 
    db_session.commit()

    result = job_dao.claim_job_for_processing(
        current_status=JobStatus.SAVED_ID, 
        new_status=JobStatus.SCRAPED_DETAILS
    )

    assert result["status"] == APIStatus.NOT_FOUND
    
    job = db_session.query(JobStub).first()
    assert job.status == JobStatus.SCRAPED_DETAILS


@pytest.fixture
def saved_job_stub(job_dao, db_session) -> JobStub:
    external_id = 999
    job_dao.save_job_stub(job_data={"external_id": external_id})
    job = db_session.query(JobStub).filter_by(external_id=external_id).one()
    return job


MOCK_FIELDS_DATA: List[Dict[str, Any]] = [
    {
        "external_field_id": "answer_text_1",
        "question": "What is your English level?",
        "answer_type": FormFieldType.TEXT,
        "answer_options": None
    },
    {
        "external_field_id": "answer_boolean_3",
        "question": "Do you have FastAPI experience?",
        "answer_type": FormFieldType.RADIO,
        "answer_options": [{"text": "Yes", "value": "1"}, {"text": "No", "value": "0"}]
    }
]


def test_save_job_form_fields_not_found(job_dao, db_session):
    non_existent_id = 9999
    result = job_dao.save_job_form_fields(non_existent_id, [])

    assert result["status"] == APIStatus.NOT_FOUND
    assert result["external_id"] == non_existent_id
    assert db_session.query(JobFormField).count() == 0


def test_save_job_form_fields_happy_path(job_dao, db_session, saved_job_stub: JobStub):
    result = job_dao.save_job_form_fields(saved_job_stub.external_id, MOCK_FIELDS_DATA)

    assert result["status"] == APIStatus.JOB_FORM_FIELDS_CREATED
    assert result["external_id"] == saved_job_stub.external_id
    assert result["id"] == saved_job_stub.id

    fields_in_db = db_session.query(JobFormField).filter(JobFormField.job_id == saved_job_stub.id).all()
    assert len(fields_in_db) == 2
    
    assert fields_in_db[0].external_field_id == "answer_text_1"
    assert fields_in_db[0].question == "What is your English level?"
    assert fields_in_db[1].external_field_id == "answer_boolean_3"
    assert fields_in_db[1].answer_options[0]["text"] == "Yes"
    
    assert saved_job_stub.status == JobStatus.FORM_FIELDS_SCRAPED


def test_save_job_form_fields_rewrites_old_data(job_dao, db_session, saved_job_stub: JobStub):
    job_id = saved_job_stub.id
    
    stale_field = JobFormField(
        job_id=job_id,
        external_field_id="stale_field_123",
        question="This should be deleted",
        answer_type=FormFieldType.TEXT,
        scraped_at=datetime.now(timezone.utc)
    )
    db_session.add(stale_field)
    db_session.commit()
    
    assert db_session.query(JobFormField).count() == 1

    db_session.expunge(stale_field)

    result = job_dao.save_job_form_fields(saved_job_stub.external_id, MOCK_FIELDS_DATA)
    
    assert result["status"] == APIStatus.JOB_FORM_FIELDS_CREATED
    
    fields_in_db = db_session.query(JobFormField).all()
    assert len(fields_in_db) == 2
    
    assert fields_in_db[0].external_field_id == "answer_text_1"
    assert fields_in_db[1].external_field_id == "answer_boolean_3"
    
    stale_field_in_db = db_session.query(JobFormField).filter_by(external_field_id="stale_field_123").first()
    assert stale_field_in_db is None

    final_job_state = db_session.query(JobStub).filter_by(id=job_id).one()
    assert final_job_state.status == JobStatus.FORM_FIELDS_SCRAPED


def test_save_job_form_fields_empty_list(job_dao, db_session, saved_job_stub: JobStub):
    job_id = saved_job_stub.id
    
    stale_field = JobFormField(job_id=job_id,
        external_field_id="stale_field_123",
        question="stale",
        answer_type=FormFieldType.TEXT,
        scraped_at=datetime.now(timezone.utc)
    )
    db_session.add(stale_field)
    db_session.commit()
    assert db_session.query(JobFormField).count() == 1

    db_session.expunge(stale_field)

    result = job_dao.save_job_form_fields(saved_job_stub.external_id, [])
    
    assert result["status"] == APIStatus.JOB_FORM_FIELDS_CREATED
    assert db_session.query(JobFormField).count() == 0

    final_job_state = db_session.query(JobStub).filter_by(id=job_id).one()
    assert final_job_state.status == JobStatus.FORM_FIELDS_SCRAPED
