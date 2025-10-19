import pytest
from unittest.mock import patch, MagicMock
from app.tasks.scrape import Scrape
from selenium.webdriver.support.ui import WebDriverWait 


class MockWebElement:
    def __init__(self, element_id):
        self._id = element_id
    
    def get_attribute(self, name):
        if name == "id":
            return self._id
        return None


@patch('app.tasks.scrape.WebDriverWait')
def test_get_external_job_ids_extraction(MockWebDriverWait, mocker):
    mock_driver = MagicMock()
    scraper_instance = Scrape(driver=mock_driver, teardown=False)
    
    mock_elements = [
        MockWebElement("job-item-101"),
        MockWebElement("job-item-202"),
        MockWebElement("job-item-303"),
    ]
    
    mock_open = mocker.patch.object(scraper_instance, 'open')
    mock_find_elements = mocker.patch.object(scraper_instance, 'find_elements', return_value=mock_elements)
    
    url = "https://mock-url.com/jobs"
    result_ids = scraper_instance.get_external_job_ids(url)

    expected_ids = [101, 202, 303]
    assert result_ids == expected_ids
    assert all(isinstance(i, int) for i in result_ids)

    mock_open.assert_called_once_with(url) 
    mock_find_elements.assert_called_once_with(
        "css selector", "ul.list-jobs li[id^='job-item-']"
    )
    
    MockWebDriverWait.return_value.until.assert_called_once()


@patch('app.tasks.scrape.WebDriverWait')
def test_get_external_job_ids_empty(MockWebDriverWait, mocker):
    mock_driver = MagicMock()
    scraper_instance = Scrape(driver=mock_driver, teardown=False)

    mock_open = mocker.patch.object(scraper_instance, 'open')
    mock_find_elements = mocker.patch.object(scraper_instance, 'find_elements', return_value=[])

    url = "https://mock-url.com/jobs"
    result_ids = scraper_instance.get_external_job_ids(url)
    assert result_ids == []

    mock_open.assert_called_once_with(url)
    mock_find_elements.assert_called_once_with(
        "css selector", "ul.list-jobs li[id^='job-item-']"
    )

    MockWebDriverWait.return_value.until.assert_called_once()


@patch('app.tasks.scrape.WebDriverWait')
def test_get_external_job_ids_mixed_data(MockWebDriverWait, mocker):
    mock_driver = MagicMock()
    scraper_instance = Scrape(driver=mock_driver, teardown=False)
    scraper_instance.logger = MagicMock()

    mock_elements = [
        MockWebElement("job-item-101"),
        MockWebElement("job-item-202"),
        MockWebElement("job-item-abc"),
        MockWebElement("job-item-4g@"),
        MockWebElement(None)
    ]

    mock_open = mocker.patch.object(scraper_instance, 'open')
    mock_find_elements = mocker.patch.object(scraper_instance, 'find_elements', return_value=mock_elements)

    url = "https://mock-url.com/jobs"
    result_ids = scraper_instance.get_external_job_ids(url)

    expected_ids = [101, 202]
    assert result_ids == expected_ids
    assert all(isinstance(i, int) for i in result_ids)

    assert scraper_instance.logger.warning.call_count == 3

    mock_open.assert_called_once_with(url) 
    mock_find_elements.assert_called_once_with(
        "css selector", "ul.list-jobs li[id^='job-item-']"
    )

    MockWebDriverWait.return_value.until.assert_called_once()
