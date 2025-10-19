import pytest
from datetime import datetime, timezone

from app.models import JobStub, JobDetails, JobForm
from app.tasks.job_dao import JobDAO


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
        "status": "scraped"
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
    assert job.status == "scraped"

    assert details.scraped_date is not None


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


def test_get_job_stub(job_dao, db_session):
    save_job = job_dao.save_job_stub(job_data={"external_id": 1})
    assert db_session.query(JobStub).count() == 1

    result = job_dao.get_job_stub()
    assert result["status"] == "claimed"
    assert result["external_id"] == 1
    assert result["id"] == save_job["id"]

    job = db_session.query(JobStub).filter_by(external_id=1).first()
    assert job is not None
    assert job.status == "scraping"


def test_job_stub_not_found(job_dao, db_session):
    result = job_dao.get_job_stub()
    assert db_session.query(JobStub).count() == 0
    assert result["status"] == "not_found"
    assert result["external_id"] == None
