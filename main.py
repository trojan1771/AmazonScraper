from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from fake_useragent import UserAgent
import urllib.robotparser

def is_allowed_by_robots(url):
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(urljoin(url, "/robots.txt"))
    rp.read()
    return rp.can_fetch("*", url)

def get_product_data(search_keyword, max_results=100):
    base_url = f"https://www.amazon.com/s?k={search_keyword.replace(' ', '+')}"
    headers = {
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Cache-Control": "max-age=0",
        "Referer": "https://www.amazon.com/",
    }

    data = []
    page_num = 1
    request_delay = 2

    while len(data) < max_results:
        url = f"{base_url}&page={page_num}"
        if is_allowed_by_robots(url):
            try:
                # Randomly select a user agent for each request
                headers["User-Agent"] = UserAgent().random

                response = requests.get(url, headers=headers)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, "html.parser")
                    products = soup.find_all("div", {"data-component-type": "s-search-result"})

                    for product in products:
                        title_elem = product.find("span", {"class": "a-text-normal"})
                        title = title_elem.text.strip() if title_elem else "N/A"

                        price_elem = product.find("span", {"class": "a-offscreen"})
                        price = price_elem.text.strip() if price_elem else "N/A"

                        rating_elem = product.find("span", {"class": "a-icon-alt"})
                        rating = rating_elem.text.split()[0] if rating_elem else "N/A"

                        reviews_elem = product.find("span", {"class": "a-size-base"})
                        reviews = reviews_elem.text if reviews_elem else "0"

                        description_elem = product.find("span", {"class": "a-size-base-plus"})
                        description = description_elem.text.strip() if description_elem else "N/A"

                        data.append({
                            "Title": title,
                            "Price": price,
                            "Rating": rating,
                            "Reviews": reviews,
                            "Description": description
                        })

                        if len(data) >= max_results:
                            break

                    # Introduce a delay with some randomness (between 3 to 6 seconds) between requests
                    time.sleep(random.uniform(3, 6))
                elif response.status_code == 503:
                    print(f"503 error encountered. Retrying after a longer delay...")
                    # Wait for a longer time before retrying
                    time.sleep(10)
                else:
                    print(f"Failed to fetch data from page {page_num}. Status code: {response.status_code}")
                    break
            except requests.exceptions.RequestException as e:
                print(f"Request failed. Retrying... Error: {e}")
                time.sleep(10)

            page_num += 1
        else:
            print(f"Access to {url} is disallowed by robots.txt. Skipping...")
            break

    return data

def save_to_csv(data, filename):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

if __name__ == "__main__":
    keyword = input("Enter the product keyword to search on Amazon: ")
    product_data = get_product_data(keyword, max_results=2000)

    if product_data:
        save_to_csv(product_data, f"{keyword}_products.csv")
    else:
        print("No data retrieved. Check your internet connection and try again.")
