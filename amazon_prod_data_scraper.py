import re
import sys
import time
import traceback
import numpy as np
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=chrome_options)

file_path = 'Data/amazon_prod_link_scraper.csv'
df_prod_links = pd.read_csv(file_path)
df_prod_links = df_prod_links.drop_duplicates(subset='Product Link')
df_prod_links = df_prod_links.dropna()
df_prod_links = df_prod_links.reset_index()

def pull_product_data(prod_link_df):
    df = prod_link_df.copy()

    df["product_name"] = ""
    df["product_price"] = ""
    df["product_ratings"] = ""
    df["product_ratings_num"] = ""
    df["product_features"] = ""
    df["product_review_link"] = ""

    for index, row in df.iterrows():
        try:
            driver.get(row["Product Link"])
            driver.implicitly_wait(10)

            # print(f'{"-"*50}\n')

            name = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '//div[@id="titleSection"]'))
            )
            # name = driver.find_element(By.XPATH, '//div[@id="titleSection"]')
            df.at[index, "product_name"] = name.text
            # print(f'{df.at[index, "product_name"]}')

            whole_price = driver.find_elements(By.XPATH, '//span[@class="a-price-whole"]')
            fraction_price = driver.find_elements(By.XPATH, '//span[@class="a-price-fraction"]')
            if whole_price != [] and fraction_price != []:
                price = '.'.join([whole_price[0].text, fraction_price[0].text])
            else:
                price = 0
            df.at[index, "product_price"] = price
            # print(f'{df.at[index, "product_price"]}')

            rating = driver.find_element(By.XPATH, '//span[@class="reviewCountTextLinkedHistogram noUnderline"]')
            df.at[index, "product_ratings"] = rating.text
            # print(f'{df.at[index, "product_ratings"]}')
            
            ratings_num = driver.find_element(By.XPATH, '//span[@id="acrCustomerReviewText"]')
            df.at[index, "product_ratings_num"] = ratings_num.text
            # print(f'{df.at[index, "product_ratings_num"]}')

            features = driver.find_elements(By.XPATH, '//ul[@class="a-unordered-list a-vertical a-spacing-mini"]/li/span[@class="a-list-item"]')
            product_features = [feature.text.strip() for feature in features]
            df.at[index, "product_features"] = '\n'.join(product_features)
            # print(f'{df.at[index, "product_features"]}')

            link = driver.find_element(By.XPATH, '//a[@data-hook="see-all-reviews-link-foot"]')
            df.at[index, "product_review_link"] = link.get_attribute("href")
            # print(f'{df.at[index, "product_review_link"]}')

            # driver.quit()

            # print(f'{"-"*50}\n')
        
        except Exception as e: 
            print(f'{"="*50}\n')
            error_info = traceback.format_exc()
            print(f'ERROR\n{error_info}\n')
            print(f'{"="*50}\n')

    return df

df_product_data = pull_product_data(df_prod_links.head(10))
# print(f'{df_product_data}')

# Define the CSV file name
file_path = 'Data/amazon_prod_data_scraper.csv'
df_product_data.to_csv(file_path, index=False)
print(f"CSV file saved at: {file_path}")