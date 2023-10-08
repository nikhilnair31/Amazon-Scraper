import re
import sys
import time
import traceback
import numpy as np
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC

chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=chrome_options)

page_url = 'https://www.amazon.com/s?rh=n%3A11056591&fs=true&ref=lp_11056591_sar'
product_asin = []
product_link = []
max_pages = 100

start_time = time.time()
for page_num in range(1, max_pages):
    driver.get(page_url)
    driver.implicitly_wait(10)
    
    items = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "s-result-item s-asin")]')))
    print(f'Page #{page_num} - Num of items: {len(items)}')
    
    for item in items:
        data_asin = item.get_attribute("data-asin")
        product_asin.append(data_asin)

        link = item.find_element(By.XPATH, './/a[@class="a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal"]').get_attribute("href")
        product_link.append(link)
    
    next_page_el = driver.find_element(By.XPATH, '//a[@class="s-pagination-item s-pagination-next s-pagination-button s-pagination-separator"]')
    page_url = next_page_el.get_attribute("href")

end_time = time.time()
elapsed_time = end_time - start_time
print(f"Time taken to complete: {elapsed_time} seconds")

curr_df = pd.DataFrame({'Product ASIN': product_asin, 'Product Link': product_link})

file_path = 'Data/amazon_prod_link_scraper.csv'
curr_df.to_csv(file_path, index=False)
print(f"CSV file saved at: {file_path}")