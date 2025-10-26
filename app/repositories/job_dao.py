# app/repositories/job_dao.py
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.models.job import JobStub, JobDetails, JobForm
from app.core.decorators import db_safe
from app.core.logger import setup_logger


class JobDAO:
    def __init__(self, session):
        self.session = session
        self.logger = setup_logger(__name__)


    @db_safe
    def save_job_stub(self, db, job_data: Dict[str, Any]) -> Dict[str, Any]:
        existing = db.query(JobStub).filter_by(external_id=job_data["external_id"]).first()
        if existing:
            self.logger.warning(f"[Duplicate] Job {job_data['external_id']} already exists, skipping insert.")
            return {"status": "duplicate", 
                    "external_id": job_data["external_id"]
            }

        stub = JobStub(
            external_id=job_data["external_id"],
            status="saved_id",
            found_at=datetime.now(timezone.utc)
        )
        db.add(stub)
        db.commit()
        db.refresh(stub)
        self.logger.info(f"[Saved] Job {stub.external_id} inserted successfully.")
        return {
            "status": "job_stub_created",
            "external_id": stub.external_id,
            "id": stub.id
        }


    @db_safe
    def save_job_details(self, db, job_details: Dict[str, Any]) -> Dict[str, Any]:
        job = db.query(JobStub).filter_by(external_id=job_details["external_id"]).first()
        if not job:
            self.logger.warning(f"[Do not exist] Job {job_details['external_id']} does not exist")
            return {"status": "not_found", 
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
        job.status = job_details["status"]

        db.commit()
        db.refresh(details)

        self.logger.info(f"[Saved] Job {job.external_id} details updated successfully.")
        return {
            "status": "job_details_updated",
            "external_id": job.external_id,
            "id": job.id
            }


    @db_safe
    def get_job_stub(self, db) -> Dict[str, Any]:
        job = db.query(JobStub).filter_by(status="saved_id").first()
        if not job:
            self.logger.warning("[Do not exist] All jobs are already scraped")
            return {
                "status": "not_found",
                "external_id": None
            }

        job.status = "scraping"
        db.commit()
        db.refresh(job)

        return {
            "status": "claimed",
            "external_id": job.external_id,
            "id": job.id
        }
