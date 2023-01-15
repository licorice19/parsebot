from time import sleep
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

URL = 'https://www.avito.ru/novotroitsk/tovary_dlya_kompyutera/komplektuyuschie/videokarty-ASgBAgICAkTGB~pm7gmmZw'
PAUSE_DURATION_SECONDS = 5
CLEANR = re.compile('<.*?>')


def main():
    driver.get(URL)
    sleep(PAUSE_DURATION_SECONDS)
    with open("page.html", "w", encoding="utf-8") as file:
        file.write(driver.page_source)
    driver.quit()
    get_items("page.html")


def get_items(file):
    with open(file, "r", encoding="utf-8") as file:
        html = file.read()
    soup = BeautifulSoup(html, "lxml")
    items = soup.find_all("div", attrs={"data-marker": "item"})
    goods = []
    for index, item in enumerate(items):
        item_url = item.find('a').get("href")
        item_price = item.find("span", attrs={"data-marker": "item-price"}).find('meta',attrs={"itemprop": "price"}).get('content')
        item_title = item.find("h3", attrs={"itemprop": "name"}).contents[0]
        goods.append(f"{index} @title {item_title} @price {item_price} @url https://avito.ru{item_url}")

    with open("urls.txt", "w", encoding="utf-8") as file:
        for good in goods:
            file.write(f"{good} \n")


if __name__ == '__main__':
    try:
        service = Service(executable_path=ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        main()
    except Exception as e:
        print(e)
    finally:
        pass
