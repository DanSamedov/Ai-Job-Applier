from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

options = Options()
options.binary_location = "/snap/chromium/3251/usr/lib/chromium-browser/chrome"
options.add_argument("--user-data-dir=/home/danas/snap/chromium/common/chromium")
options.add_argument("--profile-directory=Default")

service = Service("/usr/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://djinni.co")
print("Title:", driver.title)

time.sleep(300)
driver.quit()
