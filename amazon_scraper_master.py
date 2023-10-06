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

        self.driver = webdriver.Chrome(options = chrome_options)

        self.genObj = General()

        self.page_url = url

    def pull_links(self):
        print(f'1. Pull All Product Links')

        product_asin = []
        product_link = []
        max_pages = 5

        for page_num in range(1, max_pages):
            self.driver.get(self.page_url)
            self.driver.implicitly_wait(10)
            
            items = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "s-result-item s-asin")]')))
            # print(f'item len: {len(items)}')
            
            for item in items:
                data_asin = item.get_attribute("data-asin")
                product_asin.append(data_asin)

                link = item.find_element(By.XPATH, './/a[@class="a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal"]').get_attribute("href")
                product_link.append(link)
            
            next_page_el = self.driver.find_element(By.XPATH, '//a[@class="s-pagination-item s-pagination-next s-pagination-button s-pagination-separator"]')
            page_url = next_page_el.get_attribute("href")
        
        data_dict = {
            'Product ASIN': product_asin, 'Product Link': product_link
        }
        saved_df = pd.DataFrame(data_dict)
        saved_file_path = 'Data/amazon_prod_link_scraper.csv'
        self.genObj.save_dataframe_to_csv(saved_df, saved_file_path)

        self.driver.quit()

    def pull_data(self):
        print(f'2. Pull Product Data from Links')

        loaded_file_path = 'Data/amazon_prod_link_scraper.csv'
        loaded_df = self.genObj.load_dataframe_from_csv(loaded_file_path).copy()
        loaded_df = loaded_df.drop_duplicates(subset='Product Link')
        loaded_df = loaded_df.dropna()

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

                # print(f'{"-"*50}\n')

                # name = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, '//div[@id="titleSection"]')))
                name = self.driver.find_element(By.XPATH, '//div[@id="titleSection"]')
                loaded_df.at[index, "product_name"] = name.text
                # print(f'{loaded_df.at[index, "product_name"]}')

                # whole_price = self.driver.find_elements(By.XPATH, '//span[@class="a-price-whole"]')
                # fraction_price = self.driver.find_elements(By.XPATH, '//span[@class="a-price-fraction"]')
                # if whole_price != [] and fraction_price != []:
                #     price = '.'.join([whole_price[0].text, fraction_price[0].text])
                # else:
                #     price = 0
                price = self.driver.find_elements(By.XPATH, '//span[@class="a-price a-text-price a-size-medium apexPriceToPay"]/span[@class="a-offscreen"]')
                loaded_df.at[index, "product_price"] = price
                # print(f'{loaded_df.at[index, "product_price"]}')

                rating = self.driver.find_element(By.XPATH, '//span[@class="reviewCountTextLinkedHistogram noUnderline"]')
                loaded_df.at[index, "product_ratings"] = rating.text
                # print(f'{loaded_df.at[index, "product_ratings"]}')
                
                ratings_num = self.driver.find_element(By.XPATH, '//span[@id="acrCustomerReviewText"]')
                loaded_df.at[index, "product_ratings_num"] = ratings_num.text
                # print(f'{loaded_df.at[index, "product_ratings_num"]}')

                features = self.driver.find_elements(By.XPATH, '//ul[@class="a-unordered-list a-vertical a-spacing-mini"]/li/span[@class="a-list-item"]')
                product_features = [feature.text.strip() for feature in features]
                loaded_df.at[index, "product_features"] = '\n'.join(product_features)
                # print(f'{loaded_df.at[index, "product_features"]}')

                link = self.driver.find_element(By.XPATH, '//a[@data-hook="see-all-reviews-link-foot"]')
                loaded_df.at[index, "product_review_link"] = link.get_attribute("href")
                # print(f'{loaded_df.at[index, "product_review_link"]}')

                # self.driver.quit()

                # print(f'{"-"*50}\n')
            
            except Exception as e: 
                print(f'{"="*50}\n')
                error_info = traceback.format_exc()
                print(f'ERROR\n{error_info}\n')
                print(f'{"="*50}\n')

        saved_file_path = 'Data/amazon_prod_link_scraper.csv'
        self.genObj.save_dataframe_to_csv(loaded_df, saved_file_path)
        
        self.driver.quit()
        
    def pull_reviews(self):
        print(f'3. Pull Product Reviews')

        loaded_file_path = 'Data/amazon_prod_data_scraper.csv'
        loaded_df = self.genObj.load_dataframe_from_csv(loaded_file_path).copy()
        loaded_df = loaded_df.drop_duplicates(subset='product_review_link')
        loaded_df = loaded_df.dropna()

        for index, row in loaded_df.iterrows():
            try:
                self.driver.get(row["product_review_link"])
                self.driver.implicitly_wait(10)

                reviews = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "a-section review aok-relative")]')))
                # print(f'reviews len: {len(reviews)}')
                
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

        dict_of_data = {
            "Product ASIN": [], 
            "reviewer_name": [], "reviewer_rating": [], "reviewer_title": [], 
            "reviewer_date": [], "reviewer_verified": [], "review_body": []
        }
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
    # print(f'{user_input}')

    while(True):
        if user_input == "4":
            break
        else:
            scrape_url = 'https://www.amazon.com/s?k=phones&rh=n%3A7072561011&dc&ds=v1%3AdBDpBdof7U0nfs6nhU9Q6Fj2W7enc3cnVnsLbwsLbJ8&qid=1696625740&rnid=2941120011&ref=sr_nr_n_1'
            scraperObj = Scraper(scrape_url)
    
        if user_input == "1":
            scraperObj.pull_links()
            break
        elif user_input == "2":
            scraperObj.pull_data()
            break
        elif user_input == "3":
            scraperObj.pull_reviews()
            break
        else:
            print(f"Invalid choice '{user_input}'. Please enter valid choices (1/2/3/4).")
# endregion