from bs4 import BeautifulSoup
import requests

URL = "https://www.avito.ru/novotroitsk/tovary_dlya_kompyutera/komplektuyuschie/videokarty-ASgBAgICAkTGB~pm7gmmZw"
HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36', 'accept': '*/*'}


def get_html(url, params=None) -> requests.Response:
    r = requests.get(url, headers=HEADERS, params=params)
    return r

soup = BeautifulSoup(get_html(URL).text, "html.parser")

print(soup.find_all("h3", class_="title-root-zZCwT"))