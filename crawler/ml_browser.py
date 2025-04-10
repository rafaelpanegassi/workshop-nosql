import time
import pandas as pd
from bs4 import BeautifulSoup
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class BrowserML:
    def __init__(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--disable-setuid-sandbox")
        self.chrome_options.add_argument("--disable-web-security")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--memory-pressure-off")
        self.chrome_options.add_argument("--ignore-certificate-errors")
        self.chrome_options.add_argument("--disable-features=site-per-process")

        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
        self.drive = webdriver.Chrome(options=self.chrome_options)

    def execute_command(self, query):
        self.drive.get(f"https://lista.mercadolivre.com.br/{query.replace(' ', '-')}")
        time.sleep(5)
        html = self.drive.page_source
        soup = BeautifulSoup(html, "html.parser")
        
        # Find all product cards
        results = soup.find_all("div", class_="poly-card__content")
        
        data = []
        for result in results:
            try:
                title_text = None
                title_wrapper = result.find("h3", class_="poly-component__title-wrapper")
                
                if title_wrapper:
                    all_text = title_wrapper.get_text(strip=True)
                    title_text = all_text
                
                if not title_text:
                    title_a = result.find("a", class_="poly-component__title")
                    if title_a:
                        title_text = title_a.get_text(strip=True)
                
                price_element = result.find("span", class_="andes-money-amount__fraction")
                price = price_element.text.strip() if price_element else "No price found"
                
                link_element = result.find("a", href=True)
                link = link_element["href"] if link_element else "No link found"

                if title_text:
                    product_data = {
                        "Product": title_text,
                        "Price": price,
                        "Url": link
                    }
                    
                    data.append(product_data)
                    logger.info(f"Data Collected: {title_text} - {price}")
            except Exception as e:
                logger.error(f"Error extracting data: {e}")
        
        if not data:
            logger.warning("No products found with primary method, trying alternative...")
            
            product_items = soup.select("div.ui-search-result, div.poly-card__content")
            
            for item in product_items:
                try:
                    possible_titles = item.select("h2, h3, a.ui-search-item__title, a.poly-component__title")
                    title = next((t.get_text(strip=True) for t in possible_titles if t.get_text(strip=True)), "No title found")
                    
                    price_tags = item.select("span.price-tag-fraction, span.andes-money-amount__fraction")
                    price = next((p.get_text(strip=True) for p in price_tags if p.get_text(strip=True)), "No price found")
                    
                    url_tags = item.select("a[href]")
                    url = next((a["href"] for a in url_tags if a.has_attr("href")), "No URL found")
                    
                    data.append({
                        "Product": title,
                        "Price": price,
                        "Url": url
                    })
                    
                    logger.info(f"Alternative method - Data Collected: {title} - {price}")
                except Exception as e:
                    logger.error(f"Error in alternative extraction: {e}")
                
        self.drive.quit()
        return data

    def transform_df(self, query):
        data = self.execute_command(query)
        df = pd.DataFrame(data)
        return df


if __name__ == "__main__":
    crawler = BrowserML()
    dataframe = crawler.transform_df("notebook allienware")
    logger.info(dataframe)
    dataframe.to_csv("mercadolivre_products.csv", index=False, encoding='utf-8-sig')