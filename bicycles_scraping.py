from bs4 import BeautifulSoup
import requests, re, os, dotenv
from urllib.parse import urljoin
from os import system
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import matplotlib.pyplot as plt
import plotly.graph_objects as go


dotenv.load_dotenv()


class Bicycle:
    def __init__(self, name, price, url, reference, img="Image not available"):
        self.name = name
        self.img = img
        self.price = price
        self.current_price = price
        self.url = url
        self.reference = reference
        self.time = str(datetime.date(datetime.now()))

    def to_dict(self):
        return {
            "name": self.name,
            "img": self.img,
            "url": self.url,
            "reference": self.reference,
            "current_price": self.price,
            "prices": {self.time: self.price},
        }


# Creamos variables con los links necesarios

url = "https://www.bikingpoint.es/es/"
bicycles_endpoint = "bicicletas.html"
search_endpoint = "catalogsearch/result/?q={}"
page_endpoint = "?p={}"
bicycles_url = urljoin(url, bicycles_endpoint)
bicycles_list = []


## Crear una funcion para hacer un llamado de requests por cada pagina de bicicletas
def get_requests():
    usp_warn = False
    counter = 1
    while usp_warn == False:
        print(f"Get request page {counter}")
        response = requests.get(urljoin(bicycles_url, page_endpoint.format(counter)))
        if (
            "No podemos encontrar productos que coincida con la selección."
            in response.text
        ):
            usp_warn = True
        # Creamos la soup con BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        # Obtener el contenedor de cada bicicleta, crear cada Bycicle y guardar en una lista
        bicycles = soup.find_all("li", class_="item product product-item")
        counter += 1
        create_bicycles_list(bicycles)
        create_json()


def create_bicycles_list(bicycles):
    print("Creando lista de bicicletas")
    for bicycle in bicycles:
        bicycle_name = bicycle.find("strong", class_="product-item-name").text.strip()
        bicycle_img = bicycle.find("img")["src"]
        bicycle_href = bicycle.find("a")["href"]
        bicycle_price = get_todays_price(bicycle)
        response_href = requests.get(bicycle_href)
        if response_href.status_code == 200:
            bicycle_reference = (
                BeautifulSoup(response_href.text, "html.parser")
                .find("div", itemprop="sku")
                .text
            )
        bicycles_list.append(
            Bicycle(
                bicycle_name,
                float(bicycle_price),
                bicycle_href,
                bicycle_reference,
                bicycle_img,
            )
        )
    print(f"Cantidad de bicicletas en la lista: {len(bicycles_list)}")


# Crear un archivo json donde guardar toda la informacion de las bicicletas
def create_json():
    with open("bicycles_data_base.json", "w", encoding="utf-8") as file:
        json.dump(
            [bicycle.to_dict() for bicycle in bicycles_list],
            file,
            ensure_ascii=False,
            indent=4,
        )


# Crear funcion que obtenga el precio hoy
def get_todays_price(bicycle):
    return [
        price.text.replace("\xa0", "")
        .replace("€", "")
        .replace(".", "")
        .replace(",", ".")
        for price in bicycle.find_all("span", class_="price")
    ][0]


# Agregar precio de hoy al archivo json
def add_todays_price():
    today = str(datetime.date(datetime.now()))
    with open("bicycles_data_base.json", "r") as file:
        json_file = json.load(file.buffer)
    for bicycle in json_file:
        response_search_reference = requests.get(
            urljoin(url, search_endpoint.format(bicycle["reference"]))
        )
        if response_search_reference.status_code == 200:
            reference_soup = BeautifulSoup(
                response_search_reference.text, "html.parser"
            )
            todays_price = (
                reference_soup.find_all("span", class_="price")[0]
                .text.replace("\xa0", "")
                .replace("€", "")
                .replace(".", "")
                .replace(",", ".")
            )
            bicycle["prices"][today] = float(todays_price)
            print(json_file, "\n")
    print(json_file, "\n")
    with open("bicycles_data_base2.json", "w") as file:
        json.dump(json_file, file, indent=4, ensure_ascii="utf-8")


# Funcion para revisar si se ha cambiado el precio y en solo ese caso, agregarlo al json
def review_prices_changes():
    with open("bicycles_data_base.json", "r") as file:
        file_json = json.load(file)
        for bicycle in file_json:
            response = requests.get(
                urljoin(url, search_endpoint.format(bicycle["reference"]))
            ).text
            pattern = r'<span class="price">(.*?)</span>'
            price = re.findall(pattern, response)[0]
            clean_price = float(
                price.replace("\xa0", "")
                .replace("€", "")
                .replace(".", "")
                .replace(",", ".")
            )
            if bicycle["current_price"] != clean_price:
                bicycle["prices"][str(datetime.date(datetime.now()))] = clean_price
                bicycle["current_price"] = clean_price
        with open("bicycles_data_base.json", "w") as file:
            json.dump(file_json, file, indent=4, ensure_ascii="utf-8")


# Funcion para enviar alerta por mail de cambio de precio
def send_alert(bicycle, to=os.getenv("EMAIL")):
    from_ = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")

    mail = MIMEMultipart()
    mail["From"] = from_
    mail["To"] = to
    mail["Subject"] = "Biking Alert"
    message = f"La {bicycle['name']} ha cambiado de precio!\n{bicycle['url']}"
    mail.attach(MIMEText(message, "plain"))
    print(mail)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_, password)
        server.send_message(mail)


# Funcion para revisar si hay alguna bicicleta nueva

# Crear funcion para eliminar las bicicletas que ya no esten publicadas (o quizas pasarlas a un registro a parte para no perder los datos)


# Funcion para generar una alerta si el precio bajo
def alert_lower_price(reference, today_price):
    with open("bicycles_data_base.json", "r") as file:
        file_json = json.load(file)
        for bicycle in file_json:
            if (
                bicycle["reference"] == str(reference)
                and float(bicycle["current_price"]) > today_price
            ):
                print(
                    f"La {bicycle['name']} (referencia {bicycle['reference']}) ha bajado de precio!!"
                )


# Funcion para obtener la evolucion de el precio de una bicicleta
def get_prices(name=None, reference=None):
    if name == None and reference == None:
        print("Se debe pasar un nombre o referencia")
        return
    with open("bicycles_data_base.json", "r") as file:
        file_json = json.load(file)
        for bicycle in file_json:
            if reference != None:
                if bicycle["reference"] == str(reference):
                    for key in bicycle["prices"].keys():
                        print(f'{bicycle["name"]}:')
                        print(
                            f'The day {key} the price was {bicycle["prices"][key]:.2f}€\n'
                        )
                else:
                    print("Bicycle not found")
            else:
                if name.lower() in bicycle["name"].lower():
                    for key in bicycle["prices"].keys():
                        print(f'{bicycle["name"]}:')
                        print(
                            f'The day {key} the price was {bicycle["prices"][key]:.2f}€\n'
                        )


# Graficar los precios
## Crear un endpoint que ejecute este codigo con la bicicleta que se quiere mostrar el grafico, para no tener todos los graficos en la base de datos de antemano
def prices_graph_ploty():
    with open("bicycles_data_base.json", "r") as file:
        json_file = json.load(file)
    for bicycle in json_file:
        dates = sorted(bicycle["prices"].keys())
        prices = [bicycle["prices"][date] for date in dates]
        print(prices)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=dates, y=prices, mode="lines+markers", name="Precio")
        )

        fig.update_layout(
            title=f"Evolucion del precio - {bicycle['name']}",
            xaxis_title="Fecha",
            yaxis_title="Precio (€)",
            hovermode="x unified",
        )
        fig.write_html(f"prices_html/price_{bicycle['reference']}.html")


def prices_graph_matplotlib():
    with open("bicycles_data_base.json", "r") as file:
        json_file = json.load(file)
    for bicycle in json_file:
        dates = sorted(bicycle["prices"].keys())
        prices = [bicycle["prices"][date] for date in dates]
        print(prices)

        plt.figure(figsize=(10, 5))
        plt.plot(dates, prices, marker="o", linestyle="-", color="blue")
        plt.title(f"Evolucion del precio - {bicycle['name']}")
        plt.xlabel("Fecha")
        plt.ylabel("Precio")
        plt.savefig(f"prices_png/prices_{bicycle['reference']}.png")


system("clear")

# add_todays_price()
# get_requests()
# get_prices(name="addict")
# alert_lower_price(34687, 1000.22)
# review_prices_changes()
bicycle = {
    "name": "Bicicleta Giant TCR Advanced SL 0 Red Disc 2025",
    "img": "https://www.bikingpoint.es/pub/media/catalog/product/cache/dcd4fc1bb7121d11d822775072a9f477/3/4/34687_0_12032025_040745.jpg",
    "url": "https://www.bikingpoint.es/es/bicicleta-giant-tcr-advanced-sl-0-red-disc-2025.html",
    "reference": "34687",
    "current_price": 12499.0,
    "prices": {"2025-04-17": 12499.0},
}
send_alert(bicycle)
