# app/services/scrape.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from typing import Iterator, Dict, Any, List, Optional

from app.repositories.job_dao import JobDAO
from app.core.database import SessionLocal
from app.core.logger import setup_logger
from app.core.config import settings
from app.core.enums import ScrapeError, JobStatus, FormFieldType
from app.core.enums import APIStatus


class Scrape:
    def __init__(self,
                chrome_binary: str = settings.chrome_binary,
                profile_dir: str = settings.profile_dir,
                profile_name: str = settings.profile_name,
                driver_path: str = settings.driver_path,
                teardown: bool = False,
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


class ScrapeJobStub(Scrape):
    def __init__(self, driver: Optional[webdriver.Chrome] = None, teardown: bool = False):
        super().__init__(driver=driver, teardown=teardown)


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
            return 1

        if len(page_items) < 2:
            return 1

        try:
            return int(page_items[-2].text.strip())
        except ValueError as e:
            self.logger.error(f"[ValueError] {__name__}: {e}")
            return 1


    def iter_job_ids(self, url: str) -> Iterator[int]:
        total_pages = self.get_total_pages(url)

        for page in range(1, total_pages + 1):
            paged_url = f"{url}?page={page}"
            external_job_ids = self.get_external_job_ids(paged_url)
            yield from external_job_ids


class ScrapeJobDetails(Scrape):
    def __init__(self, driver: Optional[webdriver.Chrome] = None, teardown: bool = False):
        super().__init__(driver=driver, teardown=teardown)


    def scrape_job_details(self, external_id: int) -> Dict[str, Any]:
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


class ScrapeFormField(Scrape):
    def __init__(self, driver: Optional[webdriver.Chrome] = None, teardown: bool = False):
        super().__init__(driver=driver, teardown=teardown)


    def _parse_text_fields(self, form: WebElement) -> List[Dict[str, Any]]:
        text_fields = []
        try:
            for ta in form.find_elements(By.TAG_NAME, "textarea"):
                label_text = None 
                ta_id = ta.get_attribute("id")

                if ta_id:
                    try:
                        ta_label = form.find_element(By.CSS_SELECTOR, f"label[for='{ta_id}']")
                        if ta_label:
                            raw = ta_label.get_attribute("innerText")
                            label_text = raw.strip() if raw else None
                    except NoSuchElementException:
                        pass 

                text_fields.append ({
                    "external_field_id": ta_id,
                    "question": label_text,
                    "answer_type": FormFieldType.TEXT,
                })
        
            return text_fields

        except NoSuchElementException:
            return []


    def _parse_radio_fields(self, form: WebElement) -> List[Dict[str, Any]]:
        try:
            radio_fields = []

            labels = form.find_elements(By.CSS_SELECTOR, 'label.form-label')
            for label in labels:
                container = label.find_element(By.XPATH, './..')
                radios = container.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')

                radio_buttons = []
                for r in radios:
                    r_id = r.get_attribute("id")
                    r_value = r.get_attribute("value")

                    if r_id:
                        r_label_text = None
                        try:
                            r_label = container.find_element(By.CSS_SELECTOR, f"label[for='{r_id}']")
                            if r_label:
                                raw = r_label.get_attribute("innerText")
                                r_label_text = raw.strip() if raw else None

                            radio_buttons.append({"text": r_label_text, "value": r_value})
                        
                        except NoSuchElementException:
                            radio_buttons.append({"text": None, "value": r_value})

                question = label.get_attribute("innerText").strip()
                external_field_id = label.get_attribute("for")

                if radio_buttons:
                    radio_fields.append({
                        "external_field_id": external_field_id,
                        "question": question,
                        "answer_type": FormFieldType.RADIO,
                        "answer_options": radio_buttons
                    })

            return radio_fields

        except NoSuchElementException:
            return []


    def _parse_numeric_fields(self, form: WebElement) -> List[Dict[str, Any]]:
        try:
            numeric_fields = []
            
            number_inputs = form.find_elements(By.CSS_SELECTOR, 'input[type="number"]')

            for number_input in number_inputs:
                external_field_id = number_input.get_attribute("id")
                label_text = None

                if external_field_id:
                    try:
                        label = form.find_element(By.CSS_SELECTOR, f"label[for='{external_field_id}']")
                        label_text = label.get_attribute("innerText").strip()
                    except NoSuchElementException:
                        pass

                    numeric_fields.append({
                        "external_field_id": external_field_id,
                        "question": label_text, 
                        "answer_type": FormFieldType.NUMBER
                    })

            return numeric_fields

        except NoSuchElementException:
            return []


    def _parse_question_block(self, block: WebElement) -> List[Dict[str, Any]]:
        try:
            block.find_element(By.TAG_NAME, "textarea")
            return self._parse_text_fields(block)
        except NoSuchElementException:
            pass 
        try:
            block.find_element(By.CSS_SELECTOR, 'input[type="radio"]')
            return self._parse_radio_fields(block)
        except NoSuchElementException:
            pass
        try:
            block.find_element(By.CSS_SELECTOR, 'input[type="number"]')
            return self._parse_numeric_fields(block)
        except NoSuchElementException:
            pass
        return []


    def scrape_job_form_field(self, external_id: int):
        link = f"https://djinni.co/jobs/{external_id}"
        self.open(link)
        
        scraped_fields = []
        try:
            form = self.wait.until(EC.presence_of_element_located((By.ID, "apply_form")))
            
            question_blocks = form.find_elements(By.XPATH, ".//div[contains(@class, 'mb-')][not(.//div[contains(@class, 'mb-')])]")

            for block in question_blocks:
                field_data = self._parse_question_block(block)
                if field_data:
                    scraped_fields.extend(field_data)

            return scraped_fields

        except TimeoutException:
            return {
                "external_id": external_id,
                "link": link,
                "error": ScrapeError.TIMEOUT,
            }


if __name__ == "__main__":
    logger = setup_logger(__name__)
    dao = JobDAO(session=SessionLocal)

    with ScrapeJobStub() as scrape_job_stub_bot:
        # save id of all jobs in dashboard
        for external_id in scrape_job_stub_bot.iter_job_ids("https://djinni.co/my/dashboard/"):
            print(external_id)
            dao.save_job_stub({"external_id":external_id})
        

        # # scrape job details
        # job_info = dao.claim_job_for_processing(
        #     current_status=JobStatus.SAVED_ID,
        #     new_status=JobStatus.SCRAPING_DETAILS
        # )
        # if job_info["status"] == APIStatus.CLAIMED:
        #     external_id = job_info["external_id"]
        #     job_data = bot.scrape_job_details(external_id)
        #     if "error" not in job_data:
        #         dao.save_job_details(job_data)
        #     else:
        #         logger.warning(f"Skipping job {external_id} due to scrape error: {job_data['error']}")
        #         dao.update_job_status(
        #             external_id=external_id,
        #             new_status=JobStatus.SCRAPING_DETAILS_FAILED
        #         )
        # elif job_info["status"] == APIStatus.NOT_FOUND:
        #     logger.info("No jobs details left to scrape.")


        # # scrape job form field
        # job_info = dao.claim_job_for_processing(
        #     current_status=JobStatus.SCRAPED_DETAILS,
        #     new_status=JobStatus.SCRAPING_FORM_FIELDS
        # )
        # if job_info["status"] == APIStatus.CLAIMED:
        #     external_id = job_info["external_id"]
        #     field_data = bot.scrape_job_form_field(external_id)
        #     if "error" not in field_data:
        #         dao.save_job_form_fields(external_id=external_id, fields_data=field_data)
        #     else:
        #         logger.warning(f"Skipping job {external_id} due to scrape error: {field_data['error']}")
        #         dao.update_job_status(
        #             external_id=external_id,
        #             new_status=JobStatus.SCRAPING_FORM_FIELDS_FAILED
        #         )
        # elif job_info["status"] == APIStatus.NOT_FOUND:
        #     logger.info("No jobs left to scrape for form fields.")
