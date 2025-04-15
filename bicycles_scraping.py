from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from os import system
import json
import datetime


class Bicycle:
    def __init__(self, name, price, url, reference, img="Image not available"):
        self.name = name
        self.img = img
        self.price = price
        self.url = url
        self.reference = reference
        self.time = str(datetime.date.today())

    def to_dict(self):
        return {
            "name": self.name,
            "img": self.img,
            "url": self.url,
            "reference": self.reference,
            "prices": {
                self.time: self.price
                }
        }

# Creamos variables con los links necesarios

url = "https://www.bikingpoint.es/es/"
mtb_endpoint = "bicicletas/mtb-full-suspencion.html"
page_endpoint = "?p={}"
mtb_full_suspencion_url = urljoin(url, mtb_endpoint)
response = requests.get(mtb_full_suspencion_url)

# Creamos la soup con BeautifulSoup
if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    clean_prices = [p.text.replace("\xa0", "") for p in soup.find_all("span", class_="price")]

# Obtener el contenedor de cada bicicleta, crear cada Bycicle y guardar en una lista
bicycles_list = []
bicycles = soup.find_all("li", class_="item product product-item")
def create_bicycles_list():
    for bicycle in bicycles:
        bicycle_name = bicycle.find("strong", class_="product-item-name").text.strip()
        bicycle_img = bicycle.find("img")["src"] 
        bicycle_href = bicycle.find("a")["href"] 
        bicycle_price = get_todays_price(bicycle)
        response_href = requests.get(bicycle_href)
        if response_href.status_code == 200:
            bicycle_reference = BeautifulSoup(response_href.text, "html.parser").find("div", itemprop="sku").text
        bicycles_list.append(Bicycle(bicycle_name, float(bicycle_price), bicycle_href, bicycle_reference, bicycle_img))

# Crear un archivo json donde guardar toda la informacion de las bicicletas
def create_json():
    with open("bicycles_data_base.json", "w", encoding="utf-8") as file:
        # print(f"{bicycle.name} {bicycle.img} {bicycle.price:.2f}€ {bicycle.url} {bicycle.reference}","\n")
        json.dump([bicycle.to_dict() for bicycle in bicycles_list], file, ensure_ascii=False, indent=4)


# Crear funcion que obtenga el precio hoy
def get_todays_price(bicycle):
    return [price.text.replace('\xa0', '').replace('€', '').replace('.', '').replace(',', '.') for price in bicycle.find_all("span", class_="price")][0]

# Agregar precio de hoy al archivo json
def add_todays_price():
    search_endpoint = "catalogsearch/result/?q={}"
    with open("bicycles_data_base.json", "r") as file:
        json_file = json.load(file.buffer)
        # print(json_file)
    for bicycle in bicycles_list:
        todays_price = get_todays_price(bicycle)
        print(bicycle.bicycle_reference)
    # Entrar al json_file, buscar la referencia de cada bicicleta y "buscarla" usando el search_endpoint para obtener despues el precio de hoy
    

# Crear funcion para eliminar las bicicletas que ya no esten publicadas (o quizas pasarlas a un registro a parte para no perder los datos)


system("clear")
# create_bicycles_list()
# create_json()
add_todays_price()