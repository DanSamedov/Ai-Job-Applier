# app/models/job.py
from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, Date, DateTime,
    UniqueConstraint, JSON
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class JobStub(Base):
    __tablename__ = "job_stubs"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_job_source_external"),
    )

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, default="djinni")
    external_id = Column(Integer, nullable=False, index=True)
    status = Column(String, nullable=False)
    found_at = Column(DateTime, nullable=False)

    details = relationship("JobDetails", back_populates="stub", uselist=False, cascade="all, delete")
    fields = relationship("JobFormField", back_populates="job", cascade="all, delete")


class JobDetails(Base):
    __tablename__ = "job_details"

    id = Column(Integer, ForeignKey("job_stubs.id", ondelete="CASCADE"), primary_key=True)
    title = Column(String, nullable=True)
    company = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    link = Column(String, unique=True, nullable=True)
    scraped_at = Column(DateTime, nullable=True)

    stub = relationship("JobStub", back_populates="details")


class JobFormField(Base):
    __tablename__ = "job_form_field"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_stubs.id", ondelete="CASCADE"), nullable=False)
    
    tag = Column(String, nullable=False)
    question = Column(String, nullable=False, default="message")
    options = Column(JSON, nullable=True)

    answer = Column(Text, nullable=True) 

    scraped_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)

    job = relationship("JobStub", back_populates="fields")
