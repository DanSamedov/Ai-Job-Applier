from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from typing import Dict, Any
from datetime import datetime

from app.models import Job, JobForm
from app.database import SessionLocal


class Scrape(webdriver.Chrome):
    def __init__(self, chrome_binary="/snap/chromium/3251/usr/lib/chromium-browser/chrome",
                 profile_dir="/home/danas/snap/chromium/common/chromium",
                 profile_name="Default",
                 driver_path="/usr/bin/chromedriver",
                 teardown=False):
        self.teardown = teardown

        opts = Options()
        opts.binary_location = chrome_binary
        opts.add_argument(f"--user-data-dir={profile_dir}")
        opts.add_argument(f"--profile-directory={profile_name}")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_experimental_option("detach", True) 
        
        svc = Service(driver_path)
        super().__init__(service=svc, options=opts)


    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.teardown:
            self.quit()


    def open(self, url: str) -> None:
        self.get(url)


    def scrape_job(self, job_id: int) -> Dict[str, Any]:
        link = f"https://djinni.co/jobs/{job_id}"
        self.get(link)
        wait = WebDriverWait(self, 10)

        try:
            title = wait.until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "h1.d-flex.align-items-center.flex-wrap > span")
                )
            ).text

            job_desc = wait.until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "div.job-post__description")
                )
            ).text

            company = wait.until(
            EC.visibility_of_element_located(
                    (By.XPATH, "//a[contains(@class,'text-reset') and contains(@href,'/jobs/company-')]")
                )
            ).text.strip()

            return {
                "title": title,
                "description": job_desc,
                "company": company,
                "link": link,
                "scraped_date": datetime.utcnow(),
            }

        except TimeoutException:
            return {
                "external_id": str(job_id),
                "link": link,
                "error": "timeout_waiting_for_selectors"
            }

with Scrape() as bot:
    bot.open("https://djinni.co")
    bot.scrape_job(11232)
