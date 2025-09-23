from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
from .database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    description = Column(Text)
    link = Column(String, unique=True, nullable=False)
    posted_date = Column(Date)
    scraped_date = Column(DateTime)
    status = Column(String, default="seen")
    sent_at = Column(DateTime)

    form = relationship("JobForm", back_populates="job", cascade="all, delete")


class JobForm(Base):
    __tablename__ = "job_form"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"))
    field_name = Column(String, nullable=False)
    answer = Column(Text, nullable=False)

    job = relationship("Job", back_populates="form")
