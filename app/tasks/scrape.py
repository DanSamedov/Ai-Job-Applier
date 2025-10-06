from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging 

from app.models import JobStub, JobDetails, JobForm
from app.database import SessionLocal


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


class Scrape(webdriver.Chrome):
    def __init__(self, chrome_binary="/snap/chromium/3251/usr/lib/chromium-browser/chrome",
                 profile_dir="/home/danas/snap/chromium/common/chromium",
                 profile_name="Default",
                 driver_path="/usr/bin/chromedriver",
                 teardown=True):
        self.teardown = teardown
        self.wait = WebDriverWait(self, 10)

        opts = Options()
        opts.binary_location = chrome_binary
        opts.add_argument(f"--user-data-dir={profile_dir}")
        opts.add_argument(f"--profile-directory={profile_name}")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_experimental_option("detach", True) 
        
        svc = Service(driver_path)
        super().__init__(service=svc, options=opts)


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.teardown:
            self.quit()


    def open(self, url: str) -> None:
        self.get(url)


    def get_external_job_ids(self, url: str) -> List[int]:
        self.open(url)

        self.wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.list-jobs li[id^='job-item-']"))
        )

        items = self.find_elements(By.CSS_SELECTOR, "ul.list-jobs li[id^='job-item-']")

        external_job_ids = []
        for item in items:
            li_id = item.get_attribute("id")
            external_job_id = li_id.replace("job-item-", "")
            external_job_ids.append(int(external_job_id))

        return external_job_ids


    def get_total_pages(self, url: str) -> int:
        self.open(url)

        self.wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.pagination_with_numbers"))
        )
        page_items = self.find_elements(By.CSS_SELECTOR, "li.page-item")

        total_pages = 1
        for item in page_items:
            try:
                number = int(item.text.strip())
                if number > total_pages:
                    total_pages = number
            except ValueError:
                continue

        return total_pages


    def iter_job_ids(self, url: str):
        total_pages = self.get_total_pages(url)

        for page in range(1, total_pages + 1):
            paged_url = f"{url}my/dashboard/?page={page}"
            external_job_ids = self.get_external_job_ids(paged_url)
            yield from external_job_ids


    def scrape_job(self, external_id: int) -> Dict[str, Any]:
        link = f"https://djinni.co/jobs/{external_id}"
        self.get(link)

        try:
            title = self.wait.until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "h1.d-flex.align-items-center.flex-wrap > span")
                )
            ).text

            job_desc = self.wait.until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "div.job-post__description")
                )
            ).text

            company = self.wait.until(
            EC.visibility_of_element_located(
                    (By.XPATH, "//a[contains(@class,'text-reset') and contains(@href,'/jobs/company-')]")
                )
            ).text.strip()

            return {
                "external_id": external_id,
                "title": title,
                "company": company,
                "description": job_desc,
                "link": link,
                "status": "scraped"
            }

        except TimeoutException:
            return {
                "external_id": external_id,
                "link": link,
                "error": "timeout_waiting_for_selectors"
            }


    def save_job_stub(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        with SessionLocal() as db:
            try:
                existing = db.query(JobStub).filter_by(external_id=job_data["external_id"]).first()
                if existing:
                    logging.warning(f"[Duplicate] Job {job_data['external_id']} already exists, skipping insert.")
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
                logging.info(f"[Saved] Job {stub.external_id} inserted successfully.")
                return {
                    "status": "job_stub_created",
                    "external_id": stub.external_id,
                    "id": stub.id
                }

            except IntegrityError as e:
                db.rollback()
                logging.error(f"[IntegrityError] Could not save job {job_data.get('external_id')}: {e}")
                return {"status": "error",
                        "error": "integrity",
                        "external_id": job_data.get("external_id")
                }
            except SQLAlchemyError as e:
                db.rollback()
                logging.error(f"[DatabaseError] Failed to save job {job_data.get('external_id')}: {e}")
                return {"status": "error",
                        "error": "db",
                        "external_id": job_data.get("external_id")
                }
            except Exception as e:
                db.rollback()
                logging.exception(f"[UnexpectedError] {e}")
                return {"status": "error",
                        "error": "unexpected",
                        "external_id": job_data.get("external_id")
                }


    def save_job_details(self, job_details: Dict[str, Any]) -> Dict[str, Any]:
        with SessionLocal() as db:
            try:
                job = db.query(JobStub).filter_by(external_id=job_details["external_id"]).first()
                if not job:
                    logging.warning(f"[Do not exist] Job {job_details['external_id']} does not exist")
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

                logging.info(f"[Saved] Job {job.external_id} details updated successfully.")
                return {
                    "status": "job_details_updated",
                    "external_id": job.external_id,
                    "id": job.id
                }

            except IntegrityError as e:
                db.rollback()
                logging.error(f"[IntegrityError] Could not update job {job_details.get('external_id')} details: {e}")
                return {"status": "error",
                        "error": "integrity",
                        "external_id": job_details.get("external_id")
                }
            except SQLAlchemyError as e:
                db.rollback()
                logging.error(f"[DatabaseError] Failed to update job {job_details.get('external_id')} details: {e}")
                return {"status": "error",
                        "error": "db",
                        "external_id": job_details.get("external_id")
                }
            except Exception as e:
                db.rollback()
                logging.exception(f"[UnexpectedError] {e}")
                return {"status": "error",
                        "error": "unexpected",
                        "external_id": job_details.get("external_id")
                }


    def get_job_stub(self) -> Dict[str, Any]:
        with SessionLocal() as db:
            try:
                job = db.query(JobStub).filter_by(status="saved_id").first()
                if not job:
                    logging.warning("[Do not exist] All jobs are already scraped")
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

            except IntegrityError as e:
                db.rollback()
                logging.error(f"[IntegrityError] Could not find job: {e}")
                return {
                    "status": "error",
                    "error": "integrity",
                    "external_id": None
                }
            except SQLAlchemyError as e:
                db.rollback()
                logging.error(f"[DatabaseError] Failed to find job: {e}")
                return {
                    "status": "error",
                    "error": "db",
                    "external_id": None
                }
            except Exception as e:
                db.rollback()
                logging.exception(f"[UnexpectedError] {e}")
                return {
                    "status": "error",
                    "error": "unexpected",
                    "external_id": None
                }


with Scrape() as bot:
    job_info = bot.get_job_stub()
    if job_info["status"] == "claimed":
        job_data = bot.scrape_job(job_info["external_id"])
        if "error" not in job_data:
            bot.save_job_details(job_data)
        else:
            logging.warning(f"Skipping job {job_info['external_id']} due to scrape error: {job_data['error']}")
    elif job_info["status"] == "not_found":
        logging.info("No jobs left to scrape.")
