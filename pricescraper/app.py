from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

def configure_driver():
    """Configure and return a headless Chrome driver."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument('--disable-gpu')
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver

#Function to scrape GeMS
def scrape_gem(category, brand_name):

    try:
        gem_url = f'https://mkp.gem.gov.in/computers-0806nb/search?q={category.replace(" ", "+")}+{brand_name.replace(" ", "+")}'
        driver = configure_driver()
        products = []
        try:
            driver.get(gem_url)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.variant-wrapper")))
            time.sleep(5)  
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            for product in soup.find_all("div", {"class": "variant-wrapper"}):
                name_element = product.find("span", {"class": "variant-title"})
                price_element = product.find("span", {"class": "variant-final-price"})
                
                if name_element and price_element:
                    product_name = name_element.text.strip()
                    price_text = price_element.text.strip()
                    price_value = int(re.sub(r'[^\d]', '', price_text))
                    
                    logging.info(f"GeM Product Name: {product_name}, Price: {price_text}")
                    if 10000 <= price_value <= 80000 and brand_name.lower() in product_name.lower():
                        products.append({
                            'platform': 'GeM',
                            'name': product_name,
                            'price': price_text
                        })
                    if len(products) >= 15:
                        break
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Error scraping GeM: {e}")
        finally:
            driver.quit()
        
        if not products:
            return [{'platform': 'GeM', 'name': 'No products found', 'price': ''}]
        return products
    except Exception as e:
        logging.error(f"Error setting up GeM scraper: {e}")
        return [{'platform': 'GeM', 'name': 'Error occurred', 'price': ''}]

#Function to scrape Amazon
def scrape_amazon(category, brand_name):

    try:
        amazon_url = f'https://www.amazon.in/s?k={category.replace(" ", "+")}+{brand_name.replace(" ", "+")}'
        driver = configure_driver()
        products = []
        try:
            driver.get(amazon_url)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.s-main-slot")))
            time.sleep(5)  
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            for product in soup.find_all("div", {"data-component-type": "s-search-result"}):
                name_element = product.find("span", {"class": "a-size-medium"})
                price_symbol_element = product.find("span", {"class": "a-price-symbol"})
                price_element = product.find("span", {"class": "a-price-whole"})
                
                if name_element and price_symbol_element and price_element:
                    product_name = name_element.text.strip()
                    price_text = price_symbol_element.text.strip() + price_element.text.strip()
                    price_value = int(re.sub(r'[^\d]', '', price_element.text))
                    
                    logging.info(f"Amazon Product Name: {product_name}, Price: {price_text}")
                    
                    if 10000 <= price_value <= 80000 and brand_name.lower() in product_name.lower():
                        products.append({
                            'platform': 'Amazon',
                            'name': product_name,
                            'price': price_text
                        })
                    
                    if len(products) >= 15:
                        break
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Error scraping Amazon: {e}")
        finally:
            driver.quit()
        return products
    except Exception as e:
        logging.error(f"Error setting up Amazon scraper: {e}")
        return []

#Function to scrape Flipkart
def scrape_flipkart(category, brand_name):
    try:
        flipkart_url = f'https://www.flipkart.com/search?q={category.replace(" ", "+")}+{brand_name.replace(" ", "+")}'
        driver = configure_driver()
        products = []
        try:
            driver.get(flipkart_url)
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.tUxRFH")))
            time.sleep(5)  
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            for product in soup.find_all("div", {"class": "tUxRFH"}):
                name_element = product.find("div", {"class": "KzDlHZ"})
                price_element = product.find("div", {"class": "Nx9bqj _4b5DiR"})
                
                if name_element and price_element:
                    product_name = name_element.text.strip()
                    price_text = price_element.text.strip()
                    price_value = int(re.sub(r'[^\d]', '', price_text))
                    
                    logging.info(f"Flipkart Product Name: {product_name}, Price: {price_text}")
                    if 10000 <= price_value <= 80000 and brand_name.lower() in product_name.lower():
                        products.append({
                            'platform': 'Flipkart',
                            'name': product_name,
                            'price': price_text
                        })
                    if len(products) >= 15:
                        break
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Error scraping Flipkart: {e}")
        finally:
            driver.quit()
        return products
    except Exception as e:
        logging.error(f"Error setting up Flipkart scraper: {e}")
        return []
    

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    category = request.form.get('category')
    brand_name = request.form.get('brand_name')
    
    gem_products = scrape_gem(category, brand_name)   
    flipkart_products = scrape_flipkart(category, brand_name)
    amazon_products = scrape_amazon(category, brand_name)
    
    return render_template('index.html', amazon_products=amazon_products, flipkart_products=flipkart_products, gem_products=gem_products)

if __name__ == '__main__':
    app.run(debug=True)
