from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

def configure_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver

# Function to scrape Flipkart
def scrape_flipkart(category, brand_name):
    try:
        flipkart_url = f'https://www.flipkart.com/search?q={category.replace(" ", "+")}+{brand_name.replace(" ", "+")}'
        driver = configure_driver()
        products = []

        try:
            driver.get(flipkart_url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "tUxRFH")))
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            for product in soup.find_all("div", {"class": "tUxRFH"}):
                name_element = product.find("div", {"class": "KzDlHZ"})
                price_element = product.find("div", {"class": "Nx9bqj _4b5DiR"})

                if name_element and price_element:
                    price = int(re.sub(r'[^\d]', '', price_element.text.strip()))
                    if 10000 <= price <= 80000:
                        products.append({
                            'platform': 'Flipkart',
                            'name': name_element.text.strip(),
                            'price': price
                        })
                if len(products) >= 3:
                    break
        except Exception as e:
            logging.error(f"Error scraping Flipkart: {e}")
        finally:
            driver.quit()

        return products
    except Exception as e:
        logging.error(f"Error setting up Flipkart scraper: {e}")
        return []

# Function to scrape Amazon
def scrape_amazon(category, brand_name):
    try:
        amazon_url = f'https://www.amazon.in/s?k={category.replace(" ", "+")}+{brand_name.replace(" ", "+")}'
        driver = configure_driver()
        products = []

        try:
            driver.get(amazon_url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.s-main-slot")))
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            for product in soup.find_all("div", {"data-component-type": "s-search-result"}):
                name_element = product.find("span", {"class": "a-size-medium"})
                price_element = product.find("span", {"class": "a-price-whole"})

                if name_element and price_element:
                    price = int(re.sub(r'[^\d]', '', price_element.text.strip()))
                    if 10000 <= price <= 80000:
                        products.append({
                            'platform': 'Amazon',
                            'name': name_element.text.strip(),
                            'price': price_element.text.strip()
                        })
                if len(products) >= 3:
                    break
        except Exception as e:
            logging.error(f"Error scraping Amazon: {e}")
        finally:
            driver.quit()

        return products
    except Exception as e:
        logging.error(f"Error setting up Amazon scraper: {e}")
        return []

# Function to scrape GeM
def scrape_gem(category, brand_name):
    try:
        gem_url = f'https://gem.gov.in/search?q={category.replace(" ", "+")}+{brand_name.replace(" ", "+")}'
        driver = configure_driver()
        products = []

        try:
            driver.get(gem_url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "clearfix")))
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            for product in soup.find_all("div", {"class": "clearfix"}):
                name_element = product.find("a", href=lambda x: x and x.startswith("/Laptop notebook/"))
                price_element = product.find("span", {"class": "m-w"})

                if name_element and price_element:
                    name = name_element.get('title', '').strip()
                    price = int(re.sub(r'[^\d]', '', price_element.text.strip()))
                    if 10000 <= price <= 80000:
                        products.append({
                            'platform': 'GeM',
                            'name': name,
                            'price': price_element.text.strip()
                        })
                if len(products) >= 3:
                    break
        except Exception as e:
            logging.error(f"Error scraping GeM: {e}")
        finally:
            driver.quit()

        return products
    except Exception as e:
        logging.error(f"Error setting up GeM scraper: {e}")
        return []

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        category = request.form.get('category')
        brand_name = request.form.get('brand_name')
        logging.info(f"Category: {category}, Brand: {brand_name}")  
        if category and brand_name:
            flipkart_products = scrape_flipkart(category, brand_name)
            amazon_products = scrape_amazon(category, brand_name)
            gem_products = scrape_gem(category, brand_name)
            logging.info(f"Flipkart: {flipkart_products}")  
            logging.info(f"Amazon: {amazon_products}")  
            logging.info(f"GeM: {gem_products}")  
            return render_template('index.html', flipkart_products=flipkart_products, amazon_products=amazon_products, gem_products=gem_products)
    return render_template('index.html', flipkart_products=None, amazon_products=None, gem_products=None)

if __name__ == '__main__':
    app.run(debug=True)
