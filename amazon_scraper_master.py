# region Packages 
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
# endregion


# region Classes
class General:
    @staticmethod
    def save_dataframe_to_csv(dataframe, csv_path):
        """
        Save a DataFrame to a CSV file.
        Args:
            dataframe (pd.DataFrame): The DataFrame to be saved.
            csv_path (str): The path to the CSV file.
        Returns:
            None
        """
        dataframe.to_csv(csv_path, index=False)
        print(f"CSV file saved at: {csv_path}")

    @staticmethod
    def load_dataframe_from_csv(csv_path) -> pd.DataFrame:
        """
        Load a DataFrame from a CSV file.
        Args:
            csv_path (str): The path to the CSV file.
        Returns:
            pd.DataFrame: The loaded DataFrame.
        """
        return pd.read_csv(csv_path)

class Scraper():
    def __init__(self, url):
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        # Clear cookies
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--start-maximized")

        # Clear cache
        chrome_options.add_argument("--disable-application-cache")
        chrome_options.add_argument("--disable-gpu")

        self.driver = webdriver.Chrome(options = chrome_options)
        self.driver.maximize_window()

        self.genObj = General()

        self.page_url = url

    def measure_time(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"Time taken to complete '{func.__name__}': {elapsed_time:.0f}s")
            return result
        return wrapper

    @measure_time
    def pull_links(self):
        print(f'1. Pull All Product Links')
        
        product_asin = []
        product_link = []
        max_pages = 100

        for page_num in range(1, max_pages):
            self.driver.get(self.page_url)
            self.driver.implicitly_wait(10)
            
            items = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "s-result-item s-asin")]')))
            print(f'Page #{page_num} - Num of items: {len(items)}')
            
            for item in items:
                data_asin = item.get_attribute("data-asin")
                product_asin.append(data_asin)

                link = item.find_element(By.XPATH, './/a[@class="a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal"]').get_attribute("href")
                product_link.append(link)
            
            next_page_el = self.driver.find_element(By.XPATH, '//a[@class="s-pagination-item s-pagination-next s-pagination-button s-pagination-separator"]')
            page_url = next_page_el.get_attribute("href")

        saved_df = pd.DataFrame({
            'Product ASIN': product_asin, 'Product Link': product_link
        })
        saved_df = saved_df.drop_duplicates()
        self.genObj.save_dataframe_to_csv(saved_df, 'Data/amazon_prod_link_scraper.csv')

        self.driver.quit()

    @measure_time
    def pull_data(self, head_count):
        print(f'2. Pull Product Data from Links')

        loaded_file_path = 'Data/amazon_prod_link_scraper.csv'
        loaded_df = self.genObj.load_dataframe_from_csv(loaded_file_path).copy()
        loaded_df = loaded_df.dropna()
        loaded_df = loaded_df.head(head_count)

        loaded_df["product_name"] = ""
        loaded_df["product_price"] = ""
        loaded_df["product_ratings"] = ""
        loaded_df["product_ratings_num"] = ""
        loaded_df["product_features"] = ""
        loaded_df["product_review_link"] = ""

        for index, row in loaded_df.iterrows():
            try:
                self.driver.get(row["Product Link"])
                self.driver.implicitly_wait(10)

                name = self.driver.find_element(By.XPATH, '//div[@id="titleSection"]')
                loaded_df.at[index, "product_name"] = name.text
                
                whole_price_elements = self.driver.find_elements(By.XPATH, '//span[@class="a-price-whole"]')
                price = next((whole.text.strip() for whole in whole_price_elements if whole.text.strip()), '')
                loaded_df.at[index, "product_price"] = price
                
                rating = self.driver.find_element(By.XPATH, '//span[@class="reviewCountTextLinkedHistogram noUnderline"]')
                loaded_df.at[index, "product_ratings"] = rating.text
                
                ratings_num = self.driver.find_element(By.XPATH, '//span[@id="acrCustomerReviewText"]')
                loaded_df.at[index, "product_ratings_num"] = ratings_num.text
                
                features = self.driver.find_elements(By.XPATH, '//ul[@class="a-unordered-list a-vertical a-spacing-mini"]/li/span[@class="a-list-item"]')
                product_features = [feature.text.strip() for feature in features]
                loaded_df.at[index, "product_features"] = '\n'.join(product_features)
                
                link = self.driver.find_element(By.XPATH, '//a[@data-hook="see-all-reviews-link-foot"]')
                loaded_df.at[index, "product_review_link"] = link.get_attribute("href")

            except Exception as e: 
                print(f'{"="*50}\n')
                error_info = traceback.format_exc()
                print(f'ERROR\n{error_info}\n')
                print(f'{"="*50}\n')

        saved_file_path = 'Data/amazon_prod_data_scraper.csv'
        self.genObj.save_dataframe_to_csv(loaded_df, saved_file_path)
        
        self.driver.quit()
    
    @measure_time
    def pull_reviews(self, slice_count):
        print(f'3. Pull Product Reviews')

        loaded_file_path = 'Data/amazon_prod_data_scraper.csv'
        loaded_df = self.genObj.load_dataframe_from_csv(loaded_file_path).copy()
        loaded_df = loaded_df.drop_duplicates(subset='product_review_link')
        loaded_df = loaded_df.dropna()

        start_row = slice_count - 100
        end_row = slice_count
        loaded_df = loaded_df.iloc[start_row:end_row, :]

        dict_of_data = {
            "Product ASIN": [], 
            "reviewer_name": [], 
            "reviewer_date": [],
            "reviewer_title": [], 
            "review_body": [],
            # "reviewer_verified": [], 
            # "reviewer_rating": [],
        }
        for index, row in loaded_df.iterrows():
            try:
                next_page_link = row["product_review_link"]

                while next_page_link:
                    self.driver.get(next_page_link)
                    # self.driver.implicitly_wait(3)

                    reviews = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "a-section review aok-relative")]')))
                    print(f'reviews\n{self.driver.current_url}\nlen: {len(reviews)}')
                    
                    for review in reviews:
                        # Save each products ASIN
                        dict_of_data["Product ASIN"].append(row["Product ASIN"])

                        # Initialize empty dictionary to hold fetched data. Iterate through dictionary reviews and fetch data
                        fetched_data = {
                            "reviewer_name": './/div[@class="a-profile-content"]',
                            "reviewer_date": './/span[@data-hook="review-date"]',
                            "reviewer_title": './/a[@data-hook="review-title"]/span[not(@class)]',
                            "review_body": './/span[@data-hook="review-body"]/span',
                            # "reviewer_verified": './/span[@data-hook="avp-badge"]',
                            # "reviewer_rating": './/i[@class="a-icon a-icon-star"]/span[@class="a-icon-alt"]',
                        }
                        for column, xpath in fetched_data.items():
                            try:
                                element = WebDriverWait(review, 3).until(EC.visibility_of_element_located((By.XPATH, xpath)))
                                # element = review.find_element(By.XPATH, xpath)
                                dict_of_data[column].append(element.text)
                            except Exception as e:
                                dict_of_data[column].append("")
                                self.driver.save_screenshot(f"Other/error_screenshot_{row['Product ASIN']}_{column}.png")
                                print(f"Failed to extract {column}. XPath used: {xpath}. Error: {str(e)}")

                        # Ensure all keys have values appended in every loop to prevent unequal list lengths.
                        for key in fetched_data.keys():
                            if key not in fetched_data.keys():
                                dict_of_data[key].append("")
                    
                    try:
                        next_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, '//ul[@class="a-pagination"]//li[@class="a-last"]/a'))
                        )
                        next_page_link = next_button.get_attribute("href")
                    except Exception:
                        next_page_link = None
                        
            except Exception as e:
                print(f'{"="*50}\n')
                self.driver.save_screenshot(f"Other/error_screenshot_{row['Product ASIN']}.png")
                error_info = traceback.format_exc()
                print(f'ERROR\n{error_info}\n')
                print(f'{"="*50}\n')

        # print(f'{"-"*50}\ndict_of_data\n{dict_of_data}\n{"-"*50}\n')
        saved_df = pd.DataFrame(dict_of_data)
        saved_file_path = 'Data/amazon_prod_reviews_scraper.csv'
        self.genObj.save_dataframe_to_csv(saved_df, saved_file_path)
        
        self.driver.quit()
# endregion


# region Main
if __name__ == "__main__":
    
    initial_print = """
        Options:
        1. Pull All Product Links
        2. Pull Product Data from Links
        3. Pull Product Reviews
        4. Exit
    """
    print(initial_print)
    
    user_input = input("Enter the of option to run (e.g., '1' to pull all product links, '4' to exit etc.): ")

    while(True):
        if user_input == "4":
            break
        else:
            scrape_url = 'https://www.amazon.com/s?rh=n%3A11056591&fs=true&ref=lp_11056591_sar'
            scraperObj = Scraper(scrape_url)
    
        if user_input == "1":
            scraperObj.pull_links()
            break
        elif user_input == "2":
            input_rowcount = input("Enter number of products to pull data for (e.g. 100 to pull first 100 products, 200 to pull first 200 products etc.) ")
            scraperObj.pull_data(int(input_rowcount))
            break
        elif user_input == "3":
            input_rowcount = input("Enter the slice to pull reviews for (e.g. 100 to pull product 0 to 100, 200 to pull product 100 to 200 etc.) ")
            scraperObj.pull_reviews(int(input_rowcount))
            break
        else:
            print(f"Invalid choice '{user_input}'. Please enter valid choices (1/2/3/4).")
# endregion