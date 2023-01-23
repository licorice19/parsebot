from dotenv import load_dotenv
from time import sleep
import aiofiles
import json
import os
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
# from telebot.async_telebot import AsyncTeleBot
from telebot.async_telebot import AsyncTeleBot
from parser_module import get_items, filter_by_city, diff_search

URL = 'https://www.avito.ru/novotroitsk/tovary_dlya_kompyutera/komplektuyuschie/videokarty-ASgBAgICAkTGB~pm7gmmZw'
PAUSE_DURATION_SECONDS = 5
CITIES = ['novotroitsk', 'orenburg', 'orsk']
INTERVAL = 3600
CATEGORIES = []

load_dotenv()
TOKEN = os.environ.get("TOKEN")
PASSWORD = os.environ.get("PASSWORD")

# bot = AsyncTeleBot(TOKEN)

TOKEN = os.environ.get("TOKEN")
PASSWORD = os.environ.get("PASSWORD")

bot = AsyncTeleBot(TOKEN)

# Dictionary to keep track of active users and their current states
try:
    with open("users.json", "r") as f:
        users = json.load(f)
except FileNotFoundError:
    users = {}

@bot.message_handler(commands=['start'])
async def startup_function(message):
    chat_id = message.chat.id
    # Add the user to the dictionary with an initial state of 'inactive'
    if not users[chat_id]:
        users[chat_id] = {"state": "inactive", "data": {}}
    welcome_message = f"Welcome! To get started, type '/start_parse' to start the parsing function. Type '/stop' to stop the function. Type '/help' to display all commands"
    await bot.send_message(chat_id, welcome_message)
    async with aiofiles.open("users.json", "w") as f:
        await f.write(json.dumps(users))
        
@bot.message_handler(commands=['help'])
async def help_function(message):
    chat_id = message.chat.id
    help_message = f"Commands available: \n /start_parse: starts the parsing function \n /stop: stops the function"
    await bot.send_message(chat_id, help_message)

# Function to handle the start command
@bot.message_handler(commands=['start_parse'])
async def start_parser(message):
    chat_id = message.chat.id
    if users[chat_id]["state"] == "inactive":
        if users[chat_id]["data"]["city"]:
            city = users[chat_id]["data"]["city"]
            users[chat_id]["state"] = "active"
            await bot.send_message(chat_id, "Parser started for city: {}. Type '/stop_parser' to end the function.".format(CITIES[city]))

            while users[chat_id]["state"] == "active":
                await parser(chat_id, city)
                await asyncio.sleep(30 * 60)
    else:
        await bot.send_message(chat_id, "Parser is started")
        
@bot.message_handler(commands=['get_data'])
async def get_data(message):
    chat_id = message.chat.id
    path_file = f"users\\{chat_id}\\diff.json"
    try:
        with open("f.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        await bot.send_message(chat_id, "Data file not found.")
        return
    pages = paginate_data(data)
    current_page = 0
    while True:
        current_data = pages[current_page]
        message = ""
        for item in current_data:
            message += f"Title: {item['title']}\nPrice: {item['price']}\nURL: {item['url']}\n\n"
        await bot.send_message(chat_id, message)
        if current_page == len(pages) - 1:
            break
        current_page += 1
        await asyncio.sleep(30)

@bot.message_handler(commands=['city'])
async def city_command(message):
    # Get the chat ID of the user
    chat_id = message.chat.id
    # Get the argument passed with the command
    city = message.text.split(" ")[1]
    # Update the user's data in the dictionary
    users[chat_id]["data"]["city"] = city
    # Notify the user that the city has been set
    await bot.send_message(chat_id, f"City set to {CITIES[city]}.")
    with aiofiles.open("users.json", "w") as f:
        json.dump(users, f)

# Function to handle the stop command
@bot.message_handler(commands=['stop'])
async def stop_function(message):
    chat_id = message.chat.id
    if chat_id in users:
        # Remove the user from the dictionary
        del users[chat_id]
        await bot.send_message(chat_id, "Function stopped.")
        async with aiofiles.open("users.json", "w") as f:
            json.dump(users, f)
    else:
        await bot.send_message(chat_id, "Function is not running.")

def paginate_data(data, items_per_page=1):
    pages = []
    current_page = []
    for item in data.values():
        current_page.append(item)
        if len(current_page) == items_per_page:
            pages.append(current_page)
            current_page = []
    if current_page:
        pages.append(current_page)
    return pages


## Точка входа
def main():
    loop = asyncio.get_event_loop()
    loop.create_task(bot.polling())
    loop.run_forever()

# Основная функция парсинга
async def parser(chat_id, city):
    #пути
    path = f"users\\{chat_id}\\"
    src_page = f"{path}page.html"
    path_urls = f"{path}urls.json"
    old_path_urls = f"{path}urls_old.json"
    filtered_urls = f"{path}f.json"
    old_filtered_urls = f"{path}f_old.json"

    #загрузка вебдрайвера
    op = webdriver.ChromeOptions()
    op.add_argument('--headless')
    service = Service(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=op)
    driver.get(URL)
    
    if not os.path.exists(path):
        os.makedirs(path)

    sleep(PAUSE_DURATION_SECONDS)
    # сохранение страницы
    with open(src_page, "w", encoding="utf-8") as file:
        file.write(driver.page_source)

    # Основной парсинг
    get_items(src_page, path=path)
    filter_by_city(city, path_urls, path)
    diff_search(filtered_urls, old_filtered_urls, path)

    # удаление страницы
    if os.path.exists(f"{path}page.html"):
        os.remove(f"{path}page.html")

    driver.close()
    driver.quit()

# Точка входа
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"{e} at line {e.__traceback__.tb_lineno}")
    finally:
        pass
