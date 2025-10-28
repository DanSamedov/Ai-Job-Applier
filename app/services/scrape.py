# app/services/scrape.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from typing import Dict, Any, List, Optional

from app.repositories.job_dao import JobDAO
from app.core.database import SessionLocal
from app.core.logger import setup_logger
from app.core.config import settings
from app.utils.statuses import ScrapeError, JobStatus


class Scrape:
    def __init__(self,
                chrome_binary: str = settings.chrome_binary,
                profile_dir: str = settings.profile_dir,
                profile_name: str = settings.profile_name,
                driver_path: str = settings.driver_path,
                teardown: bool = True,
                driver: webdriver.Chrome = None):
        self.teardown = teardown
        self.logger = setup_logger(__name__)

        if driver is not None:
            self.driver = driver
        else:
            opts = Options()
            opts.binary_location = chrome_binary
            opts.add_argument(f"--user-data-dir={profile_dir}")
            opts.add_argument(f"--profile-directory={profile_name}")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_experimental_option("detach", True)

            svc = Service(driver_path)
            self.driver = webdriver.Chrome(service=svc, options=opts)

        self.wait = WebDriverWait(self.driver, 10)


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.teardown:
            self.driver.quit()


    def open(self, url: str) -> None:
        self.driver.get(url)


    def find_elements(self, *args, **kwargs):
        return self.driver.find_elements(*args, **kwargs)


    def get_external_job_ids(self, url: str) -> List[int]:
        self.open(url)

        self.wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.list-jobs li[id^='job-item-']"))
        )

        items = self.find_elements(By.CSS_SELECTOR, "ul.list-jobs li[id^='job-item-']")

        external_job_ids = []
        for item in items:
            li_id = item.get_attribute("id")
            if not li_id:
                self.logger.warning("Skipping element with no id attribute.")
                continue
            external_job_id = li_id.replace("job-item-", "")
            if external_job_id.isdigit():
                external_job_ids.append(int(external_job_id))
            else:
                self.logger.warning(f"Skipping malformed job ID '{li_id}' - not numeric.")
        return external_job_ids


    def get_total_pages(self, url: str) -> int:
        self.open(url)

        self.wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.pagination_with_numbers"))
        )
        page_items = self.find_elements(By.CSS_SELECTOR, "li.page-item")
        if not page_items:
            self.logger.warning("No page items found")
            return 0

        if len(page_items) < 2:
            return 1

        try:
            return int(page_items[-2].text.strip())
        except ValueError as e:
            self.logger.error(f"[ValueError] {__name__}: {e}")
            return 1


    def iter_job_ids(self, url: str):
        total_pages = self.get_total_pages(url)

        for page in range(1, total_pages + 1):
            paged_url = f"{url}my/dashboard/?page={page}"
            external_job_ids = self.get_external_job_ids(paged_url)
            yield from external_job_ids


    def scrape_job(self, external_id: int) -> Dict[str, Any]:
        link = f"https://djinni.co/jobs/{external_id}"
        self.open(link)

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
            }

        except TimeoutException:
            return {
                "external_id": external_id,
                "link": link,
                "error": ScrapeError.TIMEOUT
            }


if __name__ == "__main__":
    with Scrape() as bot:
        logger = setup_logger(__name__)
        dao = JobDAO(session=SessionLocal)
        # job_info = dao.claim_job_for_processing(JobStatus.SAVED_ID, JobStatus.SCRAPING)
        # if job_info["status"] == "claimed":
        #     job_data = bot.scrape_job(job_info["external_id"])
        #     if "error" not in job_data:
        #         dao.save_job_details(job_data)
        #     else:
        #         logger.warning(f"Skipping job {job_info['external_id']} due to scrape error: {job_data['error']}")
        # elif job_info["status"] == "not_found":
        #     logger.info("No jobs left to scrape.")
        while True:
            for external_id in bot.iter_job_ids("https://djinni.co/"):
                print(external_id)
                dao.save_job_stub({"external_id":external_id})
