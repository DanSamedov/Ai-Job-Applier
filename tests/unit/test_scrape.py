import pytest
from unittest.mock import MagicMock
from selenium.common.exceptions import TimeoutException

from app.services.scrape import ScrapeJobStub, ScrapeJobDetails
from app.core.enums import ScrapeError


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
def mock_driver():
    """Creates a mock Chrome driver."""
    return MagicMock()

@pytest.fixture
def stub_scraper(mocker, mock_driver):
    """Fixture for ScrapeJobStub with mocked driver and methods."""
    mock_wait_cls = mocker.patch('app.services.scrape.WebDriverWait')
    mock_wait_instance = MagicMock()
    mock_wait_cls.return_value = mock_wait_instance

    scraper = ScrapeJobStub(driver=mock_driver)
    scraper.logger = MagicMock()

    mocker.patch.object(scraper, 'open')
    mocker.patch.object(scraper, 'find_elements')
    
    return scraper

@pytest.fixture
def details_scraper(mocker, mock_driver):
    """Fixture for ScrapeJobDetails with mocked driver and methods."""
    mock_wait_cls = mocker.patch('app.services.scrape.WebDriverWait')
    mock_wait_instance = MagicMock()
    mock_wait_cls.return_value = mock_wait_instance

    scraper = ScrapeJobDetails(driver=mock_driver)
    scraper.logger = MagicMock()

    mocker.patch.object(scraper, 'open')
    
    return scraper


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
def test_get_external_job_ids(stub_scraper, job_items, expected, log_count):
    stub_scraper.find_elements.return_value = job_items

    result_job_items = stub_scraper.get_external_job_ids("http://url")

    assert result_job_items == expected
    assert all(isinstance(i, int) for i in result_job_items)

    stub_scraper.open.assert_called_once_with("http://url") 
    stub_scraper.find_elements.assert_called_once()
    stub_scraper.wait.until.assert_called_once()
    assert stub_scraper.logger.warning.call_count == log_count


@pytest.mark.parametrize(
    "page_items, expected",
    [
        ([MockPageItem("start"), MockPageItem("1"), MockPageItem("2"), MockPageItem("3"), MockPageItem("4"), MockPageItem("end")], 4),
        ([MockPageItem("start"), MockPageItem("1"), MockPageItem("end")], 1),
        ([], 1),
        ([MagicMock(text="1"), MagicMock(text="LAST"), MagicMock(text="Next")], 1),
    ]
)
def test_get_total_pages(stub_scraper, page_items, expected):
    stub_scraper.find_elements.return_value = page_items

    total_pages = stub_scraper.get_total_pages("http://url")

    assert total_pages == expected
    stub_scraper.open.assert_called_once_with("http://url") 
    stub_scraper.wait.until.assert_called_once()


@pytest.mark.parametrize(
    "total_pages, job_ids_from_page, expected",
    [
        (1, [[101, 202]], [101, 202]),
        (2, [[101, 202], [303]], [101, 202, 303]),
        (3, [[101, 202], [], [303]], [101, 202, 303]),
    ]
)
def test_iter_job_ids(stub_scraper, mocker, total_pages, job_ids_from_page, expected):
    mocker.patch.object(stub_scraper, 'get_total_pages', return_value=total_pages)
    mocker.patch.object(stub_scraper, 'get_external_job_ids', side_effect=job_ids_from_page)

    result = list(stub_scraper.iter_job_ids("http://url"))

    assert result == expected
    stub_scraper.get_total_pages.assert_called_once_with("http://url")
    assert stub_scraper.get_external_job_ids.call_count == total_pages
    for i in range(1, total_pages + 1):
        stub_scraper.get_external_job_ids.assert_any_call(f"http://url?page={i}")



def test_scrape_job_details_success(details_scraper):
    external_id = 999
    link = f"https://djinni.co/jobs/{external_id}"

    mock_title = MagicMock(text="Senior Python Developer")
    mock_desc = MagicMock(text="This is a detailed job description.")
    mock_company_text = MagicMock(strip=MagicMock(return_value="Acme Corp"))
    mock_company = MagicMock(text=mock_company_text)

    details_scraper.wait.until.side_effect = [
        mock_title,
        mock_desc,
        mock_company,
    ]

    result = details_scraper.scrape_job_details(external_id)

    details_scraper.open.assert_called_once_with(link)
    assert details_scraper.wait.until.call_count == 3

    expected_result = {
        "external_id": external_id,
        "title": "Senior Python Developer",
        "company": "Acme Corp",
        "description": "This is a detailed job description.",
        "link": link,
    }
    assert result == expected_result


def test_scrape_job_details_failure_timeout(details_scraper):
    external_id = 888
    link = f"https://djinni.co/jobs/{external_id}"

    details_scraper.wait.until.side_effect = TimeoutException("Mock timeout") 

    result = details_scraper.scrape_job_details(external_id)

    details_scraper.open.assert_called_once_with(link)

    expected_result = {
        "external_id": external_id,
        "link": link,
        "error": ScrapeError.TIMEOUT
    }
    assert result == expected_result
    details_scraper.wait.until.assert_called_once()
