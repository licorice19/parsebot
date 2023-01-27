from parser_module import json, os, get_items, filter_by_city, diff_search
from dotenv import load_dotenv
import asyncio
from time import sleep
import aiofiles
from telebot.async_telebot import AsyncTeleBot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import logging

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

URL = 'https://www.avito.ru/novotroitsk/tovary_dlya_kompyutera/komplektuyuschie/videokarty-ASgBAgICAkTGB~pm7gmmZw?cd=1&s=104'
PAUSE_DURATION_SECONDS = 10
CITIES = ['novotroitsk', 'orenburg', 'orsk']
CATEGORIES = []
TOKEN = os.environ.get("TOKEN")
PASSWORD = os.environ.get("PASSWORD")

bot = AsyncTeleBot(TOKEN)
def load_json():
    # Dictionary to keep track of active users and their current states
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
            f.close()
            return users
    except FileNotFoundError:
        users = {}
        return users
async def save_json(users):
    async with aiofiles.open("users.json", "w") as f:
        await f.write(json.dumps(users))
        await f.close()

users = load_json()
loop = asyncio.get_event_loop()

@bot.message_handler(commands=['start'])
async def startup_function(message):
    chat_id = str(message.chat.id)
    # Add the user to the dictionary with an initial state of 'inactive'
    if chat_id not in users:
        users[chat_id] = {"state": "inactive", "data": {"city":""}}
    welcome_message = f"Добро пожаловать! Пришлите мне /help чтобы посмотреть команды"
    await save_json(users)
    await bot.send_message(chat_id, welcome_message)
      
@bot.message_handler(commands=['help'])
async def help_function(message):
    chat_id = message.chat.id
    help_message = f"Данный бот поможет найти вам товар, и отследить их изменения: \n /start_parse: поиск товаров и отслесживание \n /stop: Остановить отслеживание\n /city [0-2] выбор город \n0 Новотроицк \n1 Оренбург \n2 Орск"
    await bot.send_message(chat_id, help_message)

# Function to handle the start command
@bot.message_handler(commands=['start_parse'])
async def start_parser(message):
    chat_id = str(message.chat.id)
    task_name = f"{chat_id}_parser"
    state = users[chat_id]["state"]
    city = users[chat_id]["data"]["city"]
    if state == "inactive" or not any(t.get_name() == task_name for t in asyncio.all_tasks()):
        if city in [0,1,2]:
            users[chat_id]["state"] = 'active'
            await bot.send_message(chat_id, "Парсер запущен для города: {}. Введите '/stop' чтобы остановить отслеживание.".format(CITIES[city]))
            asyncio.create_task(background_parser(chat_id, city), name=task_name)
            await save_json(users)
    else:
        await bot.send_message(chat_id, "Парсер уже запущен. /stop чтобы остановить отслеживание")
        
# @bot.message_handler(commands=['get_data'])
# async def get_data(message):
#     chat_id = message.chat.id
#     path_file = f"users\\{chat_id}\\f.json"
#     try:
#         with open(path_file, "r") as f:
#             data = json.load(f)
#     except FileNotFoundError:
#         await bot.send_message(chat_id, "Data file not found.")
#         return
#     pages = paginate_data(data)
#     current_page = 0
#     while True:
#         current_data = pages[current_page]
#         message = "Текущие предложения в вашем городе: \n\n"
#         for item in current_data:
#             message += f"Title: {item['title']}\nPrice: {item['price']}\nURL: {item['url']}\n"
#         await bot.send_message(chat_id, message)
#         if current_page == len(pages) - 1:
#             break
#         current_page += 1
#         await asyncio.sleep(1)


@bot.message_handler(commands=['city'])
async def city_command(message):
    # Get the chat ID of the user
    chat_id = str(message.chat.id)
    # Get the argument passed with the command
    city = int(message.text.split(" ")[1])
    if city in [0,1,2]:
        # Update the user's data in the dictionary
        users[chat_id]["data"]["city"] = int(city)
        # Notify the user that the city has been set
        await bot.send_message(chat_id, f"Установлен город {CITIES[city]}.")
        await save_json(users)
    else:
        await bot.send_message(chat_id, f"Неверный индекс")

# Function to handle the stop command

@bot.message_handler(commands=['stop'])
async def stop_function(message):
    chat_id = str(message.chat.id)
    task_name = f"{chat_id}_parser"
    state = users[chat_id]['state']
    if state == 'active' or any(t.get_name() == task_name for t in asyncio.all_tasks()):
        # Remove the user from the dictionary
        users[chat_id]['state'] = "inactive"
        await cancel_task(task_name)
        await bot.send_message(chat_id, "Отслеживание остановлено")
        await save_json(users)
    else:
        await bot.send_message(chat_id, "Остановка не требуется")

@bot.message_handler(commands=['debugg'])
async def debugg_function(message):
    chat_id = str(message.chat.id)
    city = CITIES[users[chat_id]["data"]["city"]]
    state = users[chat_id]["state"]
    await bot.send_message(chat_id, f"Ваши параметры: \nГород {city} \nПарсер: {state}")

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

async def background_parser(chat_id, city):
    state = users[chat_id]["state"]
    while state == 'active':
        result = await parser(chat_id, city)
        if result:
            message = "Новый товар(изменение цены): \n\n"
            for item in result:
                message += f"Название: {item['title']}\nЦена: {item['price']} руб.\nURL: {item['url']}\n\n"
            await bot.send_message(chat_id, message)
        await asyncio.sleep(10*60)

async def cancel_task(task_name):
    for task in asyncio.all_tasks():
        if task.get_name() == task_name:
            task.cancel()
            print(f"Task {task_name} has been cancelled")
            break
        else:
            print(f"Task {task_name} was not found")

async def create_task():
    for key in users.keys():
        state = users[key]["state"]
        if state == 'active':
            task_name = f"{key}_parser"
            city = users[key]["data"]['city']
            asyncio.create_task(background_parser(key, city), name=task_name)

async def start_bot():
    await create_task()
    while True:
        try:
            await bot.polling() 
        except Exception as e:
            print(f'An error occurred: {e}')

async def parser(chat_id, city):
    #пути
    path = f"users\\{chat_id}\\"
    src_page = f"{path}page.html"
    path_urls = f"{path}urls.json"
    old_path_urls = f"{path}urls_old.json"
    filtered_urls = f"{path}f.json"
    old_filtered_urls = f"{path}f_old.json"
    city_name = CITIES[city]
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
    filter_by_city(city_name, path_urls, path)
    diff = diff_search(filtered_urls, old_filtered_urls, path)

    driver.close()
    driver.quit()
    # удаление страницы
    if os.path.exists(f"{path}page.html"):
        os.remove(f"{path}page.html")

    if os.path.exists(f"{path}diff.json"):
        return diff
    else:
        return {}


if __name__ == "__main__":
    asyncio.run(start_bot(), debug=True)
