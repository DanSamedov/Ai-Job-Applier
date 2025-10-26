# app/models/job.py
from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, Date, DateTime,
    UniqueConstraint
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
    status = Column(String, nullable=False, default="found")
    found_at = Column(DateTime, nullable=False)

    details = relationship("JobDetails", back_populates="stub", uselist=False, cascade="all, delete")
    form = relationship("JobForm", back_populates="job", cascade="all, delete")


class JobDetails(Base):
    __tablename__ = "job_details"

    id = Column(Integer, ForeignKey("job_stubs.id", ondelete="CASCADE"), primary_key=True)
    title = Column(String, nullable=True)
    company = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    link = Column(String, unique=True, nullable=True)
    scraped_date = Column(DateTime, nullable=True)

    stub = relationship("JobStub", back_populates="details")


class JobForm(Base):
    __tablename__ = "job_form"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_stubs.id", ondelete="CASCADE"), nullable=False)
    field_name = Column(String, nullable=False, default="message")
    answer = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)

    job = relationship("JobStub", back_populates="form")
