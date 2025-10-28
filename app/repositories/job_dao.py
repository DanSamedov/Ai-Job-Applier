# app/repositories/job_dao.py
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.models.job import JobStub, JobDetails, JobForm
from app.core.decorators import db_safe
from app.core.logger import setup_logger
from app.core.enums import JobStatus, APIStatus


class JobDAO:
    def __init__(self, session):
        self.session = session
        self.logger = setup_logger(__name__)


    @db_safe
    def save_job_stub(self, db, job_data: Dict[str, Any]) -> Dict[str, Any]:
        existing = db.query(JobStub).filter_by(external_id=job_data["external_id"]).first()
        if existing:
            self.logger.warning(f"[Duplicate] Job {job_data['external_id']} already exists, skipping insert.")
            return {"status": APIStatus.DUPLICATE, 
                    "external_id": job_data["external_id"]
            }

        stub = JobStub(
            external_id=job_data["external_id"],
            status=JobStatus.SAVED_ID,
            found_at=datetime.now(timezone.utc)
        )
        db.add(stub)
        db.commit()
        db.refresh(stub)
        self.logger.info(f"[Saved] Job {stub.external_id} inserted successfully.")
        return {
            "status": APIStatus.JOB_STUB_CREATED,
            "external_id": stub.external_id,
            "id": stub.id
        }


    @db_safe
    def save_job_details(self, db, job_details: Dict[str, Any]) -> Dict[str, Any]:
        job = db.query(JobStub).filter_by(external_id=job_details["external_id"]).first()
        if not job:
            self.logger.warning(f"[Do not exist] Job {job_details['external_id']} does not exist")
            return {"status": APIStatus.NOT_FOUND, 
                    "external_id": job_details["external_id"]
            }

        if job.details:
            details = job.details
        else:
            details = JobDetails(id=job.id)
            db.add(details)

        details.title = job_details["title"]
        details.company = job_details["company"]
        details.description = job_details["description"]
        details.link = job_details["link"]
        details.scraped_date = datetime.now(timezone.utc)

        job.status = JobStatus.SCRAPED

        db.commit()
        db.refresh(details)

        self.logger.info(f"[Saved] Job {job.external_id} details updated successfully.")
        return {
            "status": APIStatus.JOB_DETAILS_UPDATED,
            "external_id": job.external_id,
            "id": job.id
            }


    @db_safe
    def claim_job_for_processing(self, db, current_status: JobStatus, new_status: JobStatus) -> Dict[str, Any]:
        job = db.query(JobStub).filter_by(status=current_status).with_for_update(skip_locked=True).first()
        if not job:
            self.logger.warning(f"[Not Found] No available jobs with status '{current_status.value}'")
            return {
                "status": APIStatus.NOT_FOUND,
                "external_id": None
            }

        job.status = new_status
        db.commit()
        db.refresh(job)

        self.logger.info(f"[Claimed] Job {job.external_id} status set to '{new_status.value}'")
        return {
            "status": APIStatus.CLAIMED,
            "external_id": job.external_id,
            "id": job.id
        }
