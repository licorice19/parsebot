import json
import os
from bs4 import BeautifulSoup
from collections import OrderedDict

async def get_items(file, path): 
    urls_file = f"{path}urls.json"
    urls_old_file = f"{path}urls_old.json"

    if os.path.exists(urls_file):
        if os.path.exists(urls_old_file):
            os.remove(urls_old_file)
        os.rename(urls_file, urls_old_file)

    with open(file, "r", encoding="utf-8") as file:
        html = file.read()

    soup = BeautifulSoup(html, "lxml")
    items = soup.find_all("div", attrs={"data-marker": "item"})
    goods = {}

    for index, item in enumerate(items):
        item_url = item.find('a').get("href")
        item_price = item.find("span", attrs={"data-marker": "item-price"}).find('meta', attrs={"itemprop": "price"}).get('content')
        item_title = item.find("h3", attrs={"itemprop": "name"}).contents[0]
        goods[index] = {'title':item_title, 'price':item_price, 'url': f"https://www.avito.ru{item_url}"}
    with open(urls_file, "w", encoding="utf-8") as file:
        goods = OrderedDict(sorted(goods.items()))
        json.dump(goods, file)


# фильтрация текстового файла по городу
async def filter_by_city(city, file_path, output_path):
    city_code = city
    filtered_items = {}

    # Rename the previous filtered file to a backup
    filtered_file = f"{output_path}f.json"
    old_filtered_file = f"{output_path}f_old.json"
    if os.path.exists(filtered_file):
        if os.path.exists(old_filtered_file):
            os.remove(old_filtered_file)
        os.rename(filtered_file, old_filtered_file)

    # Open and read the input file
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
        
        # Iterate through the data and filter by city
        for key, value in data.items():
            if city_code in value['url']:
                filtered_items[key] = value

    # Sort the filtered items
    filtered_items = OrderedDict(sorted(filtered_items.items()))

    # Write the filtered items to a new file
    filtered_file = f"{output_path}/f.json"
    with open(filtered_file, "w", encoding="utf-8") as file:
        json.dump(filtered_items, file)

async def json_compare(json1, json2):
    try:
        f1 = open(json1, "r", encoding="utf-8")
        f2 = open(json2, "r", encoding="utf-8")
        dict1 = json.load(f1)
        dict2 = json.load(f2)
        if dict1 and dict2:
            diff =  [x for x in dict1.values() if x not in dict2.values()] + [x for x in dict2.values() if x not in dict1.values()]
            print(diff)
        else:
            print("The dict1 or dict2 are empty")
    except FileNotFoundError as e:
        print(f"{e} : Invalid file path")
    except json.decoder.JSONDecodeError as e:
        print(f"{e} : Invalid json format")
    except Exception as e:
        print(e)
    finally:
        f1.close()
        f2.close()


# Выборка различающихся строк из двух файлов
async def diff_search(file1, file2, path):
    diff_file = f"{path}diff.json"
    try:
        if os.path.exists(file1) and os.path.exists(file2):
            with open(file1, "r", encoding="utf-8") as f1, open(file2, "r", encoding="utf-8") as f2:
                dict1 = json.load(f1)
                dict2 = json.load(f2)
                diff =  [x for x in dict1.values() if x not in dict2.values()] + [x for x in dict2.values() if x not in dict1.values()]
                if diff:
                    with open(diff_file, "w", encoding="utf-8") as file:
                        json.dump(diff, file)
                    return diff
    except FileNotFoundError as e:
        print(f"{e} : Invalid file path")
    except json.decoder.JSONDecodeError as e:
        print(f"{e} : Invalid json format")
    except Exception as e:
        print(e)
