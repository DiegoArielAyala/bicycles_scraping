from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from os import system
import json
from datetime import datetime
import matplotlib.pyplot as plt
import plotly.graph_objects as go



class Bicycle:
    def __init__(self, name, price, url, reference, img="Image not available"):
        self.name = name
        self.img = img
        self.price = price
        self.url = url
        self.reference = reference
        self.time = str(datetime.date(datetime.now()))

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
bicycles_endpoint = "bicicletas.html"
page_endpoint = "?p={}"
bicycles_url = urljoin(url, bicycles_endpoint)

## Crear una funcion para hacer un llamado de requests por cada pagina de bicicletas
def get_requests():
    usp_warn = False
    counter = 1
    while usp_warn == False:
        print(f"Get request page {counter}")
        response = requests.get(urljoin(bicycles_url, page_endpoint.format(counter)))
        if "No podemos encontrar productos que coincida con la selección." in response.text:
            usp_warn = True
        # Creamos la soup con BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        # Obtener el contenedor de cada bicicleta, crear cada Bycicle y guardar en una lista
        bicycles = soup.find_all("li", class_="item product product-item")
        counter+=1
        create_bicycles_list(bicycles)

bicycles_list = []
def create_bicycles_list(bicycles):
    print("Creando lista de bicicletas")
    for bicycle in bicycles:
        bicycle_name = bicycle.find("strong", class_="product-item-name").text.strip()
        bicycle_img = bicycle.find("img")["src"] 
        bicycle_href = bicycle.find("a")["href"] 
        bicycle_price = get_todays_price(bicycle)
        response_href = requests.get(bicycle_href)
        if response_href.status_code == 200:
            bicycle_reference = BeautifulSoup(response_href.text, "html.parser").find("div", itemprop="sku").text
        bicycles_list.append(Bicycle(bicycle_name, float(bicycle_price), bicycle_href, bicycle_reference, bicycle_img))
    print(f"Cantidad de bicicletas en la lista: {len(bicycles_list)}")

# Crear un archivo json donde guardar toda la informacion de las bicicletas
def create_json():
    with open("bicycles_data_base.json", "w", encoding="utf-8") as file:
        json.dump([bicycle.to_dict() for bicycle in bicycles_list], file, ensure_ascii=False, indent=4)


# Crear funcion que obtenga el precio hoy
def get_todays_price(bicycle):
    return [price.text.replace('\xa0', '').replace('€', '').replace('.', '').replace(',', '.') for price in bicycle.find_all("span", class_="price")][0]

# Agregar precio de hoy al archivo json
def add_todays_price():
    search_endpoint = "catalogsearch/result/?q={}"
    today = str(datetime.date(datetime.now()))
    with open("bicycles_data_base.json", "r") as file:
        json_file = json.load(file.buffer)
    for bicycle in json_file:
        response_search_reference = requests.get(urljoin(url, search_endpoint.format(bicycle["reference"])))
        if response_search_reference.status_code == 200:
            reference_soup = BeautifulSoup(response_search_reference.text, "html.parser")
            todays_price = reference_soup.find_all("span", class_="price")[0].text.replace('\xa0', '').replace('€', '').replace('.', '').replace(',', '.')
            bicycle["prices"][today] = float(todays_price)
            print(json_file, "\n")
    print(json_file, "\n")
    with open("bicycles_data_base2.json", "w") as file:
        json.dump(json_file, file, indent=4, ensure_ascii="utf-8")

    

# Crear funcion para eliminar las bicicletas que ya no esten publicadas (o quizas pasarlas a un registro a parte para no perder los datos)

bicicleta  = {
        "name": "Bicicleta Scott Spark 900 Ultimate Evo Axs",
        "img": "https://www.bikingpoint.es/pub/media/catalog/product/cache/dcd4fc1bb7121d11d822775072a9f477/2/7/27229_0_07032025_040602.jpg",
        "url": "https://www.bikingpoint.es/es/bicicleta-scott-spark-900-ultimate-evo-axs-2022.html",
        "reference": "27229",
        "prices": {
            "2025-04-15": 8219.4,
            "2025-04-16": 8219.4
        }
    }
print(bicicleta.keys())

# Graficar los precios
    ## Crear un endpoint que ejecute este codigo con la bicicleta que se quiere mostrar el grafico, para no tener todos los graficos en la base de datos de antemano
def prices_graph():
    with open("bicycles_data_base2.json", "r") as file:
        json_file = json.load(file)
    for bicycle in json_file:
        dates = sorted(bicycle["prices"].keys())
        prices = [bicycle["prices"][date] for date in dates]
        print(prices)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=prices, mode="lines+markers", name="Precio"))

        fig.update_layout(
            title=f"Evolucion del precio - {bicycle['name']}",
            xaxis_title="Fecha",
            yaxis_title = "Precio (€)",
            hovermode="x unified"
        )
        fig.write_html(f"prices_html/price_{bicycle['reference']}.html")
    
        
        plt.figure(figsize=(10, 5))
        plt.plot(dates, prices, marker="o", linestyle="-", color="blue")
        plt.title(f"Evolucion del precio - {bicycle['name']}")
        plt.xlabel("Fecha")
        plt.ylabel("Precio")
        plt.savefig(f"prices_png/prices_{bicycle['reference']}.png")
        


system("clear")
# create_bicycles_list()
# create_json()
# add_todays_price()
# prices_graph()
# get_requests()
print(len(bicycles_list))
