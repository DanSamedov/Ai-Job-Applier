import pytest
from unittest.mock import patch, MagicMock
from selenium.common.exceptions import TimeoutException

from app.tasks.scrape import Scrape


class MockJobItem:
    def __init__(self, element_id):
        self._id = element_id
    
    def get_attribute(self, name):
        if name == "id":
            return self._id
        return None


class MockPageItem:
    def __init__(self, text_content):
        self.text = text_content

    def strip(self):
        return self.text.strip()


@pytest.fixture
def scraper_with_mocks(mocker):
    mock_driver = MagicMock()
    mock_wait_constructor = mocker.patch('app.tasks.scrape.WebDriverWait')
    mock_wait_instance = MagicMock()
    mock_wait_constructor.return_value = mock_wait_instance

    scraper = Scrape(driver=mock_driver, teardown=False)
    scraper.logger = MagicMock()
    mock_open = mocker.patch.object(scraper, 'open')
    mock_find_elements = mocker.patch.object(scraper, 'find_elements')
    return scraper, mock_open, mock_find_elements


# get_external_job_ids
@pytest.mark.parametrize(
    "job_items, expected, log_count",
    [
        ([MockJobItem("job-item-101"), MockJobItem("job-item-202"), MockJobItem("job-item-303")],
            [101, 202, 303], 0),
        ([], [], 0),
        ([MockJobItem("job-item-101"), MockJobItem("job-item-202"), MockJobItem("job-item-abc"),
            MockJobItem("job-item-4g@"), MockJobItem(None)], [101, 202], 3),
    ]
)
def test_get_external_job_ids(scraper_with_mocks, job_items, expected, log_count):
    scraper, mock_open, mock_find_elements = scraper_with_mocks
    mock_find_elements.return_value = job_items

    result_job_items = scraper.get_external_job_ids("http://url")
    assert result_job_items == expected
    assert all(isinstance(i, int) for i in result_job_items)

    mock_open.assert_called_once_with("http://url") 
    mock_find_elements.assert_called_once_with(
        "css selector", "ul.list-jobs li[id^='job-item-']"
    )
    scraper.wait.until.assert_called_once()

    assert scraper.logger.warning.call_count == log_count


# get_total_pages
@pytest.mark.parametrize(
    "page_items, expected, log_type",
    [
        ([MockPageItem("start_arrow"), MockPageItem("1"), MockPageItem("2"), MockPageItem("3"), MockPageItem("4"), MockPageItem("end_arrow")], 4, None),
        ([MockPageItem("start_arrow"), MockPageItem("1"), MockPageItem("end_arrow")], 1, None),
        ([], 0, "warning"),
        ([MagicMock(text="1"), MagicMock(text="LAST_PAGE"), MagicMock(text="Next")], 1, "error"),
    ]
)
def test_get_total_pages(scraper_with_mocks, page_items, expected, log_type):
    scraper, mock_open, mock_find_elements = scraper_with_mocks
    mock_find_elements.return_value = page_items

    total_pages = scraper.get_total_pages("http://url")
    assert total_pages == expected

    mock_open.assert_called_once_with("http://url") 
    mock_find_elements.assert_called_once_with("css selector", "li.page-item")
    scraper.wait.until.assert_called_once()

    if log_type:
        getattr(scraper.logger, log_type).assert_called_once()


# iter_job_ids
@pytest.mark.parametrize(
    "total_pages, job_ids_from_page, expected",
    [
        (0, [], []),
        (1, [[101, 202]], [101, 202]),
        (2, [[101, 202], [303]], [101, 202, 303]),
        (3, [[101, 202], [], [303]], [101, 202, 303]),
    ]
)
def test_iter_job_ids(scraper_with_mocks, total_pages, job_ids_from_page, expected):
    scraper, _, _ = scraper_with_mocks
    scraper.get_total_pages = MagicMock(return_value=total_pages)
    scraper.get_external_job_ids = MagicMock(side_effect=job_ids_from_page)

    result = list(scraper.iter_job_ids("http://url"))

    assert result == expected
    scraper.get_total_pages.assert_called_once_with("http://url")
    assert scraper.get_external_job_ids.call_count == total_pages
    for i in range(1, total_pages + 1):
        scraper.get_external_job_ids.assert_any_call(f"http://urlmy/dashboard/?page={i}")


# scrape_job
def test_scrape_job_success(scraper_with_mocks):
    scraper, mock_open, mock_find_elements = scraper_with_mocks
    external_id = 999
    link = f"https://djinni.co/jobs/{external_id}"

    mock_title = MagicMock(text="Senior Python Developer")
    mock_desc = MagicMock(text="This is a detailed job description.")
    mock_company_text = MagicMock(strip=MagicMock(return_value="Acme Corp"))
    mock_company = MagicMock(text=mock_company_text)

    scraper.wait.until.side_effect = [
        mock_title,
        mock_desc,
        mock_company,
    ]

    result = scraper.scrape_job(external_id)

    scraper.open.assert_called_once_with(link)
    assert scraper.wait.until.call_count == 3

    expected_result = {
        "external_id": external_id,
        "title": "Senior Python Developer",
        "company": "Acme Corp",
        "description": "This is a detailed job description.",
        "link": link,
        "status": "scraped"
    }
    assert result == expected_result


def test_scrape_job_failure_timeout(scraper_with_mocks):
    scraper, mock_open, mock_find_elements = scraper_with_mocks
    external_id = 888
    link = f"https://djinni.co/jobs/{external_id}"

    scraper.wait.until.side_effect = TimeoutException("Mock timeout") 

    result = scraper.scrape_job(external_id)

    scraper.open.assert_called_once_with(link)

    expected_result = {
        "external_id": external_id,
        "link": link,
        "error": "timeout_waiting_for_selectors"
    }
    assert result == expected_result
    scraper.wait.until.assert_called_once()
