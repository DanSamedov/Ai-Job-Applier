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
