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

def pull_product_reviews(prod_reviews_link_df):
    dict_of_data = {
        "Product ASIN": [], 
        "reviewer_name": [], "reviewer_rating": [], "reviewer_title": [], 
        "reviewer_date": [], "reviewer_verified": [], "review_body": []
    }

    for index, row in prod_reviews_link_df.iterrows():
        try:
            driver.get(row["product_review_link"])
            driver.implicitly_wait(10)

            reviews = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "a-section review aok-relative")]')))
            print(f'reviews len: {len(reviews)}')
            for review in reviews:
                # Save each products ASIN
                dict_of_data["Product ASIN"].append(row["Product ASIN"])

                # Initialize empty dictionary to hold fetched data. Iterate through dictionary reviews and fetch data
                fetched_data = {
                    "reviewer_name": './/div[@class="a-profile-content"]',
                    "reviewer_date": './/span[@data-hook="review-date"]',
                    "reviewer_verified": './/span[@data-hook="avp-badge"]',
                    "review_body": './/div[@class="a-row a-spacing-small review-data"]',
                }
                for column, xpath in fetched_data.items():
                    try:
                        element = review.find_element(By.XPATH, xpath)
                        dict_of_data[column].append(element.text)
                    except NoSuchElementException:
                        dict_of_data[column].append("")
                        print(f"{column} not found, filling with an empty string.")

                #FIXME: GET REVIEWER'S RATING 
                rating_element = review.find_element(By.XPATH, './/i[@data-hook="review-star-rating"]/span[@class="a-icon-alt"]')
                dict_of_data["reviewer_rating"].append(rating_element.text)

                title_element = review.find_element(By.XPATH, './/a[@data-hook="review-title"]/span[not(@class)]')
                dict_of_data["reviewer_title"].append(title_element.text)

        except Exception as e:
            print(f'{"="*50}\n')
            error_info = traceback.format_exc()
            print(f'ERROR\n{error_info}\n')
            print(f'{"="*50}\n')

    df = pd.DataFrame(dict_of_data)
    return df

file_path = 'Data/amazon_prod_data_scraper.csv'
df_prod_data = pd.read_csv(file_path)
df_prod_data = df_prod_data.drop_duplicates(subset='product_review_link')
df_prod_data = df_prod_data.dropna()

df_product_reviews = pull_product_reviews(df_prod_data.head(5))

file_path = 'Data/amazon_prod_reviews_scraper.csv'
df_product_reviews.to_csv(file_path, index=False)
print(f"CSV file saved at: {file_path}")