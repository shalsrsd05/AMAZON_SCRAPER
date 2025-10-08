from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from datetime import datetime  # Added for timestamp

# ---------- Scraper Function ----------
def scrape_amazon(product, pages, file_format, filename, min_price=None, min_rating=None):
   
 # Setup Chrome options
    options = Options()
    options.add_argument("--headless")  # Run browser in background
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid detection

    driver = webdriver.Chrome(options=options)
    all_products = []
    for page in range(1, pages + 1):
        url = f"https://www.amazon.in/s?k={product}&page={page}"
        print(f"\nScraping page {page}: {url}")
        driver.get(url)
       
 # Wait until product containers load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
                )
            )
        except:
            print(f"No results found on page {page}")
            continue
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for item in soup.select("div[data-component-type='s-search-result']"):
            # Title
            title = item.h2.get_text(strip=True) if item.h2 else None
            # Price
            price_elem = item.select_one("span.a-price span.a-offscreen")
            if price_elem:
                try:
                    price = int(price_elem.get_text(strip=True).replace("₹", "").replace(",", ""))
                except ValueError:
                    price = None
            else:
                price = None        
 # Rating
            rating_elem = item.select_one("span.a-icon-alt")
            if rating_elem:
                try:
                    rating = float(rating_elem.get_text(strip=True).split()[0])
                except ValueError:
                    rating = None
            else:
                rating = None
            
# Image URL
            image = item.select_one("img.s-image")
            image_url = image["src"] if image else None
            # Product URL
            link_elem = item.select_one("h2 a")
            if link_elem and link_elem.get("href"):
                product_url = "https://www.amazon.in" + link_elem.get("href")
            else:
              
  # fallback: try any link inside the item
                alt_link = item.select_one("a.a-link-normal")
                product_url = "https://www.amazon.in" + alt_link.get("href") if alt_link else None
            if title:
                product_data = {
                    "Title": title,
                    "Price (₹)": price,
                    "Rating": rating,
                    "Image URL": image_url,
                    "Product URL": product_url,
                    "Scraped On": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Added timestamp
                }
                # Apply filters if provided
                if min_price and (price is None or price < min_price):
                    continue
                if min_rating and (rating is None or rating < min_rating):
                    continue
                all_products.append(product_data)
        # Random delay to mimic human browsing
        time.sleep(random.uniform(2, 5))
    driver.quit()
   
 # ---------- Save Data ----------
    df = pd.DataFrame(all_products)
    if file_format == "csv":
        df.to_csv(filename + ".csv", index=False, encoding="utf-8-sig")
    elif file_format == "json":
        df.to_json(filename + ".json", orient="records", indent=4)
    elif file_format == "excel":
        df.to_excel(filename + ".xlsx", index=False)
    else:
        print("Invalid format. Saving as CSV by default.")
        df.to_csv(filename + ".csv", index=False, encoding="utf-8-sig")
    print(f"\nScraping finished! {len(df)} products saved as {filename}.{file_format}")

# ---------- Main ----------
if __name__ == "__main__":
    print("\n===== Amazon Scraper =====")
    product = input("Enter product name to search: ").strip().replace(" ", "+")
    pages = int(input("Enter number of pages to scrape: "))
    file_format = input("Choose file format (csv/json/excel): ").lower().strip()
    filename = input("Enter output file name (without extension): ").strip()
    # Filtering options
    apply_filter = input("Do you want to filter products? (yes/no): ").lower().strip()
    min_price = None
    min_rating = None
    if apply_filter == "yes":
        price_input = input("Enter minimum price (or press Enter to skip): ").strip()
        rating_input = input("Enter minimum rating (1-5, or press Enter to skip): ").strip()
        min_price = int(price_input) if price_input else None
        min_rating = float(rating_input) if rating_input else None
    scrape_amazon(product, pages, file_format, filename, min_price, min_rating)
