from dotenv import load_dotenv
from time import sleep
import re
import os
import asyncio
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import mainbot as mybot

URL = 'https://www.avito.ru/novotroitsk/tovary_dlya_kompyutera/komplektuyuschie/videokarty-ASgBAgICAkTGB~pm7gmmZw'
PAUSE_DURATION_SECONDS = 5
CITIES = ['novotroitsk', 'orenburg', 'orsk']
INTERVAL = 3600
CATEGORIES = []


def main():
    parser(-1, 0)

# Основная функция парсинга
def parser(chat_id, city):
    path = f"users\\{chat_id}\\"

    op = webdriver.ChromeOptions()
    op.add_argument('--headless')
    service = Service(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=op)
    driver.get(URL)
    if not os.path.exists(path):
        os.makedirs(path)

    sleep(PAUSE_DURATION_SECONDS)
    with open(f"{path}page.html", "w", encoding="utf-8") as file:
        file.write(driver.page_source)

    get_items(f"{path}page.html", path=path)
    filter_by_city(city, f"{path}urls.txt", path)
    diff_search(f"{path}f.txt", f"{path}f_old.txt", path)

    if os.path.exists(f"{path}page.html"):
        os.remove(f"{path}page.html")
    driver.close()
    driver.quit()

def get_items(file, path): 
    urls_file = f"{path}urls.txt"
    urls_old_file = f"{path}urls_old.txt"

    if os.path.exists(urls_file):
        if os.path.exists(urls_old_file):
            os.remove(urls_old_file)
        os.rename(urls_file, urls_old_file)

    with open(file, "r", encoding="utf-8") as file:
        html = file.read()

    soup = BeautifulSoup(html, "lxml")
    items = soup.find_all("div", attrs={"data-marker": "item"})
    goods = []

    for item in items:
        item_url = item.find('a').get("href")
        item_price = item.find("span", attrs={"data-marker": "item-price"}).find('meta', attrs={"itemprop": "price"}).get('content')
        item_title = item.find("h3", attrs={"itemprop": "name"}).contents[0]
        goods.append(f"@title {item_title} @price {item_price} @url https://avito.ru{item_url}")

    with open(urls_file, "w", encoding="utf-8") as file:
        for good in goods:
            file.write(f"{good} \n")

# фильтрация текстового файла по городу
def filter_by_city(city, file, path):
    items = []
    f_file = f"{path}f.txt"
    f_old_file = f"{path}f_old.txt"

    if os.path.exists(f_file):
        if os.path.exists(f_old_file):
            os.remove(f_old_file)
        os.rename(f_file, f_old_file)

    with open(file, "r", encoding="utf-8") as file:
        while True:
            line = file.readline()
            if re.findall(CITIES[city], line):
                items.append(line)
            if not line:
                write_list_in_file(items, f"{path}f.txt")
                break

# запись листа в файл
def write_list_in_file(list, filename):
    with open(filename, "w", encoding="utf-8") as file:
        for item in list:
            file.write(f"{item}")

# Выборка различающихся строк из двух файлов
def diff_search(file1, file2, path):
    file = f"{path}diff.txt"
    if os.path.exists(file1):
        if os.path.exists(file2):
            f1 = open(file1, "r", encoding="utf-8")
            f2 = open(file2, "r", encoding="utf-8")
            list1 = f1.readlines()
            list2 = f2.readlines()
            diff_lines = list(set(list1) - set(list2))
            if os.path.exists(file):
                os.remove(file)
            if diff_lines:
                write_list_in_file(diff_lines, file)


# Точка входа
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"{e} at line {e.__traceback__.tb_lineno}")
    finally:
        pass
