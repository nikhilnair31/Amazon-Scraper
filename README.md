# Amazon Scraper
## Overview
This Python script is a web scraper designed to extract product information from Amazon using Selenium, a popular web automation library. It allows you to search for products on Amazon, scrape details such as product name, price, and ratings, and save the data to a CSV file for further analysis.

## Prerequisites
Before using this Amazon scraper, ensure you have the following dependencies installed:
- Python 3.11
- Selenium
- Chrome WebDriver
- Google Chrome

### Usage
Clone this repository to your local machine or download the script `amazon_scraper.py`:
```
git clone https://github.com/your-username/amazon-scraper.git
```
Place the downloaded Chrome WebDriver executable in the same directory as `amazon_scraper.py`.

Open amazon_scraper.py in a text editor and configure the following variables:

AMAZON_URL: The URL of the Amazon search results page you want to scrape.
MAX_PAGES: The number of pages of search results to scrape.
OUTPUT_FILE: The name of the CSV file where the scraped data will be saved.

### Run the script:

```
python amazon_scraper.py
```
The script will open a headless Chrome browser, perform the specified search, scrape the data, and save it to the CSV file.

## Disclaimer
This script is intended for educational and personal use only. Web scraping may violate Amazon's Terms of Service or the website's policies. Be sure to review and comply with the website's terms and conditions before using this script.

## License
This project is licensed under the MIT License - see the LICENSE file for details.