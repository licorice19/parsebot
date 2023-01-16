from time import sleep
import re
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

URL = 'https://www.avito.ru/novotroitsk/tovary_dlya_kompyutera/komplektuyuschie/videokarty-ASgBAgICAkTGB~pm7gmmZw'
PAUSE_DURATION_SECONDS = 5
CITIES = ['novotroitsk', 'orenburg', 'orsk']
CATEGORIES = []


def main():
    html_get()
    get_items("page.html")
    filter_by_city()
    diff_search(f"{CITIES[0]}.txt", f"old_{CITIES[0]}.txt")

# получение html страницы
def html_get():
    driver.get(URL)
    sleep(PAUSE_DURATION_SECONDS)
    with open("page.html", "w", encoding="utf-8") as file:
        file.write(driver.page_source)

# получение списка товаров
def get_items(file):
    if (os.path.exists("urls.txt")):
        if (os.path.exists("old_urls.txt")):
            os.remove('old_urls.txt')
        os.rename('urls.txt', 'old_urls.txt')

    with open(file, "r", encoding="utf-8") as file:
        html = file.read()
    soup = BeautifulSoup(html, "lxml")
    items = soup.find_all("div", attrs={"data-marker": "item"})
    goods = []
    for index, item in enumerate(items):
        item_url = item.find('a').get("href")
        item_price = item.find("span", attrs={"data-marker": "item-price"}).find(
            'meta', attrs={"itemprop": "price"}).get('content')
        item_title = item.find("h3", attrs={"itemprop": "name"}).contents[0]
        goods.append(
            f"@title {item_title} @price {item_price} @url https://avito.ru{item_url}")

    with open("urls.txt", "w", encoding="utf-8") as file:
        for good in goods:
            file.write(f"{good} \n")

# фильтрация текстового файла по городу
def filter_by_city(city=0, file="urls.txt"):
    items = []

    if (os.path.exists(f"{CITIES[city]}.txt")):
        if (os.path.exists(f"old_{CITIES[city]}.txt")):
            os.remove(f"old_{CITIES[city]}.txt")
        os.rename(f"{CITIES[city]}.txt", f"old_{CITIES[city]}.txt")

    with open(file, "r", encoding="utf-8") as file:
        while True:
            line = file.readline()
            if re.findall(CITIES[city], line):
                items.append(line)
            if not line:
                write_list_in_file(items, f"{CITIES[city]}.txt")
                break

# запись листа в файл
def write_list_in_file(list, filename):
    with open(filename, "w", encoding="utf-8") as file:
        for item in list:
            file.write(f"{item}")

# Выборка различающихся строк из двух файлов
def diff_search(file1, file2):
    if os.path.exists(file1):
        if os.path.exists(file2):
            f1 = open(file1, "r", encoding="utf-8")
            f2 = open(file2, "r", encoding="utf-8")
            list1 = f1.readlines()
            list2 = f2.readlines()
            diff_lines = list(set(list1) - set(list2))
            write_list_in_file(diff_lines, f"diff_of_{file1}&{file2}")

#Точка входа
if __name__ == '__main__':
    try:
        service = Service(executable_path=ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        main()
    except Exception as e:
        print(e)
    finally:
        driver.close()
        driver.quit()
