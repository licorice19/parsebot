from parser_module import json, os, get_items, filter_by_city, diff_search
from dotenv import load_dotenv
import asyncio
from time import sleep
import aiofiles
from telebot.async_telebot import AsyncTeleBot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.util import quick_markup
import logging

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

URL = 'https://www.avito.ru'
PAUSE_DURATION_SECONDS = 10
cities = {"Новотроицк":'novotroitsk', "Оренбург":'orenburg', "Орск":'orsk'}
categories = {"Комп":
    {"Компл":
        {"Вид.карты":"tovary_dlya_kompyutera/komplektuyuschie/videokarty",
        "Проц-ы":"tovary_dlya_kompyutera/komplektuyuschie/protsessory", 
        "Мат-платы": "tovary_dlya_kompyutera/komplektuyuschie/materinskie_platy", 
        "Оп-память": "tovary_dlya_kompyutera/komplektuyuschie/operativnaya_pamyat", 
        "СО":"tovary_dlya_kompyutera/komplektuyuschie/sistemy_ohlazhdeniya", 
        "Кор-сы":"tovary_dlya_kompyutera/komplektuyuschie/korpusy",
        "Контр-ы":"tovary_dlya_kompyutera/komplektuyuschie/kontrollery",
        "Зв.карты": "tovary_dlya_kompyutera/komplektuyuschie/zvukovye_karty",
        "ЖД": "tovary_dlya_kompyutera/komplektuyuschie/zhestkie_diski",
        "БП": "tovary_dlya_kompyutera/komplektuyuschie/bloki_pitaniya"
        },
    "Мониторы":"tovary_dlya_kompyutera/monitory",
    },
    "Авто":"avtomobili"
}
TOKEN = os.environ.get("TOKEN")

bot = AsyncTeleBot(TOKEN)
city_button_markup = InlineKeyboardMarkup()

#Основные кнопки
start_parse_btn = InlineKeyboardButton(text="Запустить отслеживание", callback_data="func|start_parser")
sel_category_btn = InlineKeyboardButton(text="Выбрать категорию товара", callback_data="func|sel_category")
city_btn = InlineKeyboardButton(text="Выбрать город", callback_data="func|city")
stop_btn = InlineKeyboardButton(text="Остановить отслеживание", callback_data="func|stop")
show_all_btn = InlineKeyboardButton(text="Текущие предложения", callback_data="func|show_all")
help_btn = InlineKeyboardButton(text="Помощь", callback_data="func|help")
profile_btn = InlineKeyboardButton(text="Мои настройки", callback_data="func|profile")
menu_btn = InlineKeyboardButton(text="Меню", callback_data="func|menu")

for key, value in cities.items():
    city_button_markup.add(InlineKeyboardButton(text=key, callback_data=value))

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


@bot.message_handler(commands=['start'])
async def startup_function(message):
    chat_id = str(message.chat.id)
    # Add the user to the dictionary with an initial state of 'inactive'
    if chat_id not in users:
        users[chat_id] = {"state": "inactive", "data": {"city":"", "category":""}}
        welcome_message = f"Добро пожаловать! Выберите свой город."
        await save_json(users)
        await bot.send_message(chat_id, welcome_message, reply_markup = city_button_markup)

# @bot.callback_query_handler(func=lambda call: call.data.startswith('city'))
@bot.callback_query_handler(func=lambda call: call)
async def callback_start_city(call):
    call_data = call.data
    chat_id = str(call.message.chat.id)
    pass
    if call_data in cities.values(): #cities
        markup = InlineKeyboardMarkup(row_width=1).add(sel_category_btn, start_parse_btn, menu_btn)
        users[chat_id]["data"]["city"] = call.data
        await bot.send_message(chat_id, f"Город изменен. Выберите действие", reply_markup=markup)
        await save_json(users)
        try:
            await bot.delete_message(chat_id, call.message.message_id)
        except Exception as e:
            print(f'An error occurred: {e}')

    if call_data.split('|')[1] == "city": # city
        await bot.send_message(chat_id, f"Выберите город:", reply_markup = city_button_markup)
        await save_json(users)
        try:
            await bot.delete_message(chat_id, call.message.message_id)
        except Exception as e:
            print(f'An error occurred: {e}')

    if call_data.split('|')[1] == "start_parser": #start parse
        await start_parser_callback(call)
        await save_json(users)
        try:
            await bot.delete_message(chat_id, call.message.message_id)
        except Exception as e:
            print(f'An error occurred: {e}')

    if call_data.split('|')[1] == "menu": #menu
        await menu_callback(call)
        try:
            await bot.delete_message(chat_id, call.message.message_id)
        except Exception as e:
            print(f'An error occurred: {e}')

    if call_data.split('|')[1] == "sel_category": #category
        await sel_category_callback(call)
        try:
            await bot.delete_message(chat_id, call.message.message_id)
        except Exception as e:
            print(f'An error occurred: {e}')

    if call_data.split('|')[1] == "sc": #рекурсия
        await sel_category_callback(call)
        try:
            await bot.delete_message(chat_id, call.message.message_id)
        except Exception as e:
            print(f'An error occurred: {e}')

    if call_data.split('|')[1] == "stop": #stop
        await stop_function_callback(call)
        try:
            await bot.delete_message(chat_id, call.message.message_id)
        except Exception as e:
            print(f'An error occurred: {e}')

    if call_data.split('|')[1] == "profile": #profile
        pass

    if call_data.split('|')[1] == "help": #help
        pass

    if call_data.split('|')[1] == "show_all": #show all
        pass

async def menu_callback(call):
    chat_id = str(call.message.chat.id)
    task_name = f"{chat_id}_parser"
    state = users[chat_id]["state"]
    if state == "inactive" or not any(t.get_name() == task_name for t in asyncio.all_tasks()):
        markup = InlineKeyboardMarkup(row_width=1).add(start_parse_btn, sel_category_btn, city_btn, show_all_btn, profile_btn, help_btn)
    else:
        markup = InlineKeyboardMarkup(row_width=1).add(stop_btn, sel_category_btn, city_btn, show_all_btn, profile_btn, help_btn)
    await bot.send_message(chat_id, f"Главное меню", reply_markup=markup)


# callback функция запуска отcлеживания
async def start_parser_callback(call):
    chat_id = str(call.message.chat.id)
    if users[chat_id]:
        task_name = f"{chat_id}_parser"
        state = users[chat_id]["state"]
        city = users[chat_id]["data"]["city"]
        category = users[chat_id]["data"]["category"]
        city_name = await get_key(city, cities)
        if state == "inactive" or not any(t.get_name() == task_name for t in asyncio.all_tasks()):
            if city in cities.values():
                if category:
                    markup = InlineKeyboardMarkup(row_width=1).add(stop_btn, menu_btn)
                    users[chat_id]["state"] = 'active'
                    await bot.send_message(chat_id, f"Парсер запущен для города: {city_name}. Выберите действие", reply_markup=markup)
                    await save_json(users)
                    asyncio.create_task(background_parser(chat_id, city, category), name=task_name)
                else:
                    markup = InlineKeyboardMarkup(row_width=1).add(sel_category_btn, menu_btn)
                    await bot.send_message(chat_id, "Не выбрана категория.", reply_markup=markup)
            else:
                markup = InlineKeyboardMarkup(row_width=1).add(city_btn, menu_btn)
                await bot.send_message(chat_id, "Не выбран город.", reply_markup=markup)
        else:
            markup = InlineKeyboardMarkup(row_width=1).add(city_btn, menu_btn)
            await bot.send_message(chat_id, "Парсер уже запущен.", reply_markup=markup)

async def stop_function_callback(call):
    chat_id = str(call.message.chat.id)
    markup = InlineKeyboardMarkup(row_width=1).add(menu_btn)
    if users[chat_id]:
        task_name = f"{chat_id}_parser"
        state = users[chat_id]['state']
        if state == 'active' or any(t.get_name() == task_name for t in asyncio.all_tasks()):
            # Remove the user from the dictionary
            users[chat_id]['state'] = "inactive"
            await folder_contents_remove(f"users\\{chat_id}")
            await cancel_task(task_name)
            await bot.send_message(chat_id, "Отслеживание остановлено", reply_markup=markup)
            await save_json(users)
        else:
            await bot.send_message(chat_id, "Остановка не требуется", reply_markup=markup)

async def sel_category_callback(call):
    chat_id = str(call.message.chat.id)
    call_test = call.data.split('|')[0]
    if call.data.split('|')[0] == "func":
        markup = InlineKeyboardMarkup(row_width=1)
        for key, value in categories.items():
            category = categories[key]
            if str(type(category)) == "<class 'dict'>":
                markup.add(InlineKeyboardButton(text=key, callback_data=f"ct|sc|{key}"))
            else:
                markup.add(InlineKeyboardButton(text=key, callback_data=f"lk|sc|{key}"))

        markup.add(menu_btn)
        await bot.send_message(chat_id, f"Категории", reply_markup=markup)

    if call.data.split('|')[0] == 'lk':
        key = call.data.split('|')[2]
        users[chat_id]["data"]["category"] = categories[key]
        print(categories[key])
        markup = InlineKeyboardMarkup(row_width=1).add(start_parse_btn, menu_btn)
        await bot.send_message(chat_id, f"Выбрана категория: {key}", reply_markup=markup)
        await save_json(users)

    if call.data.split('|')[0] == 'lk1':
        cat = call.data.split('|')[2]
        key = call.data.split('|')[3]
        users[chat_id]["data"]["category"] = categories[cat][key]
        print(categories[cat][key])
        markup = InlineKeyboardMarkup(row_width=1).add(start_parse_btn, menu_btn)
        await bot.send_message(chat_id, f"Выбрана категория: {key}", reply_markup=markup)
        await save_json(users)
    
    if call.data.split('|')[0] == 'lk2':
        subcat = call.data.split('|')[2]
        cat = call.data.split('|')[3]
        key = call.data.split('|')[4]
        users[chat_id]["data"]["category"] = categories[subcat][cat][key]
        print(categories[subcat][cat][key])
        markup = InlineKeyboardMarkup(row_width=1).add(start_parse_btn, menu_btn)
        await bot.send_message(chat_id, f"Выбрана категория: {key}", reply_markup=markup)
        await save_json(users)

    if call.data.split('|')[0] == "ct":
        cat = call.data.split('|')[2] 
        markup = InlineKeyboardMarkup(row_width=1)
        pass
        for key, value in categories[cat].items():
            category = categories[cat][key]
            if str(type(category)) == "<class 'dict'>":
                markup.add(InlineKeyboardButton(text=key, callback_data=f"ct1|sc|{cat}|{key}"))
            else:
                markup.add(InlineKeyboardButton(text=key, callback_data=f"lk1|sc|{cat}|{key}"))
        markup.add(menu_btn)
        await bot.send_message(chat_id, f"Категории", reply_markup=markup)

    if call.data.split('|')[0] == "ct1":
        cat = call.data.split('|')[3]
        subcat = call.data.split('|')[2]
        markup = InlineKeyboardMarkup(row_width=2)
        for key, value in categories[subcat][cat].items():
            category = categories[subcat][cat][key]
            if str(type(category)) == "<class 'dict'>":
                markup.add(InlineKeyboardButton(text=key, callback_data=f"ct2|sc|{subcat}|{cat}|{key}"))
            else:
                markup.add(InlineKeyboardButton(text=key, callback_data=f"lk2|sc|{subcat}|{cat}|{key}"))
        markup.add(menu_btn)
        await bot.send_message(chat_id, f"Категории", reply_markup=markup)

async def get_key(value, dict):
    for k, v in dict.items():
        if v == value:
            return k

@bot.message_handler(commands=['help'])
async def help_function(message):
    chat_id = message.chat.id
    users[chat_id] = {"state": "inactive", "data": {"city":"", "category":""}}
    markup = InlineKeyboardMarkup(row_width=1).add(menu_btn)
    await save_json(users)
    help_message = f"Данный бот поможет найти вам товар, и отследить их изменения."
    await bot.send_message(chat_id, help_message, reply_markup=markup)

async def folder_contents_remove(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for file in files:
            os.remove(os.path.join(root, file))

# @bot.message_handler(commands=['start_parse'])
# async def start_parser(message):
#     pass
    # chat_id = str(message.chat.id)
    # if users[chat_id]:
    #     task_name = f"{chat_id}_parser"
    #     state = users[chat_id]["state"]
    #     city = users[chat_id]["data"]["city"]
    #     if state == "inactive" or not any(t.get_name() == task_name for t in asyncio.all_tasks()):
    #         if city in [0,1,2]:
    #             users[chat_id]["state"] = 'active'
    #             await bot.send_message(chat_id, "Парсер запущен для города: {}. Введите '/stop' чтобы остановить отслеживание.".format(cities[city]))
    #             asyncio.create_task(background_parser(chat_id, city), name=task_name)
    #             await save_json(users)
    #     else:
    #         await bot.send_message(chat_id, "Парсер уже запущен. /stop чтобы остановить отслеживание")
        
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


# @bot.message_handler(commands=['city'])
# async def city_command(message):
#     # Get the chat ID of the user
#     chat_id = str(message.chat.id)
#     if users[chat_id]:
#         # Get the argument passed with the command
#         message = f"Выберите свой город."
#         await bot.send_message(chat_id, message, reply_markup = city_button_markup)

# Function to handle the stop command

# @bot.message_handler(commands=['stop'])
# async def stop_function(message):
#     chat_id = str(message.chat.id)
#     if users[chat_id]:
#         task_name = f"{chat_id}_parser"
#         state = users[chat_id]['state']
#         if state == 'active' or any(t.get_name() == task_name for t in asyncio.all_tasks()):
#             # Remove the user from the dictionary
#             users[chat_id]['state'] = "inactive"
#             await cancel_task(task_name)
#             await bot.send_message(chat_id, "Отслеживание остановлено")
#             await save_json(users)
#         else:
#             await bot.send_message(chat_id, "Остановка не требуется")

@bot.message_handler(commands=['debugg'])
async def debugg_function(message):
    chat_id = str(message.chat.id)
    if chat_id == '317131814':
        city = users[chat_id]["data"]["city"]
        state = users[chat_id]["state"]
        await bot.send_message(chat_id, f"Ваши параметры: \nГород {city} \nПарсер: {state}")

# def paginate_data(data, items_per_page=1):
#     pages = []
#     current_page = []
#     for item in data.values():
#         current_page.append(item)
#         if len(current_page) == items_per_page:
#             pages.append(current_page)
#             current_page = []
#     if current_page:
#         pages.append(current_page)
#     return pages

async def background_parser(chat_id, city, category):
    state = users[chat_id]["state"]
    markup = InlineKeyboardMarkup(row_width=1).add(menu_btn)
    sleep(3)
    while state == 'active':
        result = await parser(chat_id, city, category)
        if result:
            message = "Новый товар(изменение цены): \n\n"
            for item in result:
                message += f"Название: {item['title']}\nЦена: {item['price']} руб.\nURL: {item['url']}\n\n"
            await bot.send_message(chat_id, message, reply_markup=markup)
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
            category = users[key]["data"]['category']
            asyncio.create_task(background_parser(key, city, category), name=task_name)

async def start_bot():
    await create_task()
    while True:
        try:
            await bot.polling(non_stop=True) 
        except Exception as e:
            print(f'An error occurred: {e}')




async def parser(chat_id, city, category):
    #пути
    if category == "avtomobili":
        source_url = f"{URL}/{city}/{category}?cd=1&radius=200&localPriority=1"
    else:
        source_url = f"{URL}/{city}/{category}"
    
    print(source_url)
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
    driver.get(source_url)
    
    if not os.path.exists(path):
        os.makedirs(path)

    sleep(PAUSE_DURATION_SECONDS)
    # сохранение страницы
    with open(src_page, "w", encoding="utf-8") as file:
        file.write(driver.page_source)

    # Основной парсинг
    await get_items(src_page, path=path)
    await filter_by_city(city, path_urls, path)
    if category == "avtomobili":
        diff = await diff_search(path_urls, old_path_urls, path)
    else:
        diff = await diff_search(filtered_urls, old_filtered_urls, path)

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
