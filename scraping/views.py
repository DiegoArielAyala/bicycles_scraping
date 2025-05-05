from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
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
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.db import IntegrityError
from .models import Bicycle, PriceHistory
from .forms import BicycleForm, PriceHistoryForm
from django.utils import timezone

dotenv.load_dotenv()


class Bicycle2:
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


def home(request):
    return render(request, "home.html")


def signup(request):
    if request.method == "GET":
        return render(request, "signup.html", {"form": UserCreationForm()})
    else:
        print(request.POST)
        if request.POST["password1"] == request.POST["password2"]:
            try:
                user = User.objects.create_user(
                    username=request.POST["username"],
                    password=request.POST["password1"],
                )
                print(user)
                user.save()
                login(request, user)
                return redirect("home")
            except IntegrityError:
                return render(
                    request,
                    "signup.html",
                    {"form": UserCreationForm(), "error": "User already exists"},
                )
        else:
            return render(
                request,
                "signup.html",
                {"form": UserCreationForm(), "error": "Password not match"},
            )


def signin(request):
    form = AuthenticationForm(request)
    print(request)
    if request.method == "GET":
        return render(request, "signin.html", {"form": form})
    else:
        try:
            user = authenticate(
                request,
                username=request.POST["username"],
                password=request.POST["password"],
            )
            login(request, user)
            return redirect("home")
        except:
            return render(
                request,
                "signin.html",
                {"form": form, "error": "User or password incorrect."},
            )


def signout(request):
    logout(request)
    return redirect("home")


def create_bicycles(bicycles):
    print("Creando lista de bicicletas")
    bicycles_list = []
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
            # Buscar en la db si existe esa referencia
            try:
                get_object_or_404(Bicycle, reference=bicycle_reference)
                print(f"Referencia {bicycle_reference} ya existe en la base de datos")
                continue
            except:
                print("Bicycle not exist")
                bicycle_form = BicycleForm(
                    {
                        "name": bicycle_name,
                        "img": bicycle_img,
                        "current_price": bicycle_price,
                        "url": bicycle_href,
                        "reference": bicycle_reference,
                    }
                )
                new_bicycle = bicycle_form.save()
                print(f"\n\nnew_bicycle.id:\n {new_bicycle.id}")
                print(f"\n\nnew_bicycle:\n {new_bicycle}")
                try:
                    price_history = PriceHistory(
                        bicycle=new_bicycle,
                        date=datetime.now().date(),
                        price=bicycle_price,
                    )
                    price_history.save()
                    print(f"\n\nprice_history:\n {price_history}")
                except:
                    print("Error creating price_history")

def extract_bicycles_from_web(request):
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
        try:
            create_bicycles(bicycles)
        except ValueError:
            return render(request, "home.html", {"error": "Bicycle saving completed"})
    return render(request, "create_bicycles.html")


def add_todays_price(request):
    today = str(datetime.date(datetime.now()))
    bicycles_list = get_list_or_404(Bicycle)
    for bicycle in bicycles_list:
        print(bicycle.reference)
    return render(request, "add_todays_price.html")

    """
    with open("bicycles_db.json", "r") as file:
        json_file = json.load(file.buffer)
    for bicycle in json_file:
        response_search_reference = requests.get(
            urljoin(url, search_endpoint.format(bicycle["reference"]))
        )
        print(bicycle["reference"])
        if response_search_reference.status_code == 200:
            reference_soup = BeautifulSoup(
                response_search_reference.text, "html.parser"
            )
            if "La búsqueda no ha devuelto ningún resultado." in reference_soup.text:
                print(f"Reference {bicycle['reference']} was deleted")
                # Agregar funcion para eliminar la referencia del json
                continue
            else:
                todays_price = (
                    reference_soup.find_all("span", class_="price")[0]
                    .text.replace("\xa0", "")
                    .replace("€", "")
                    .replace(".", "")
                    .replace(",", ".")
                )

            bicycle["prices"][today] = float(todays_price)
    with open("bicycles_db.json", "w") as file:
        json.dump(json_file, file, indent=4, ensure_ascii="utf-8")

    """










# Pedir datos en consola para ejecutar las funciones que desee el cliente
def exe_app():
    search = input(
        "Search a bicycle or enter a reference (For example: Scott Spark or 30480):\n"
    )
    try:
        int(search)
        prices_graph_matplotlib(search)
    except:
        bicycles_searched = []
        with open("bicycles_db.json", "r") as file:
            file_json = json.load(file)
            for bicycle in file_json:
                if search.lower() in bicycle["name"].lower():
                    bicycles_searched.append(
                        f"{bicycle['name']} => Reference: {bicycle['reference']}"
                    )
        if len(bicycles_searched) == 0:
            print("There are no matches")
            exe_app()
        elif len(bicycles_searched) == 1:
            pattern = r"Reference: (\d+)"
            reference = re.search(pattern, bicycles_searched[0]).group(1)
        else:
            for bicycle_searched in sorted(bicycles_searched):
                print(bicycle_searched)
            reference = input("Enter the reference of the desired bicycle:\n")
        prices_graph_matplotlib(reference)
    email_subscription = input("Do you want to subscribe to prices alerts? Y/N:\n")
    if email_subscription.lower() == "y" or "yes":
        print("email_subscription")
        email = input("Enter your Gmail email:\n")
        pattern = r"\b[\w.%+-]+@gmail.[\w{2,4}?]+\b"
        while not re.search(pattern, email):
            email = input("Enter a valid Gmail email:\n")
        print(email)
        correct_email = input("The email is correct? Y/N:\n")
        while correct_email.lower() == "n" or "no":
            email = input("Enter your Gmail email:\n")
            print(email)
            correct_email = input("The email is correct? Y/N:\n")
        send_subscript_confirm(email, reference)
    elif email_subscription.lower() == "n" or "no":
        print("No email subscription")
    else:
        print("Invalid entry")


# Recibir la confirmacion de la suscripcion al mail
def send_subscript_confirm(email, reference):
    with open("subscription_list.json", "r") as file:
        file_json = json.load(file)
        new_user = True
        for user in file_json:
            if user["email"] == email:
                new_user = False
                if reference not in user["reference"]:
                    user["reference"].append(reference)
            print(user)
        if new_user:
            file_json.append({"email": email, "reference": [reference]})
        print(file_json)
        with open("subscription_list.json", "w") as file:
            json.dump(file_json, file, indent=4, ensure_ascii="utf-8")

    print("Subscribed")
    from_ = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")

    mail = MIMEMultipart()
    mail["From"] = from_
    mail["To"] = email
    mail["Subject"] = "Alerts subscription"
    message = "You have been subscribed successfully."
    mail.attach(MIMEText(message, "plain"))
    print(mail)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_, password)
        server.send_message(mail)


# Envia codigo de validacion de correo:
def send_code_to_email(email):
    pass


# Hace un llamado requests.get por cada pagina de bicicletas y crea el archivo json.
def create_json_file():
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
        bicycles_list = create_bicycles_list(bicycles)
        create_json(bicycles_list)


def create_bicycles_list(bicycles):
    print("Creando lista de bicicletas")
    bicycles_list = []
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
            Bicycle2(
                bicycle_name,
                float(bicycle_price),
                bicycle_href,
                bicycle_reference,
                bicycle_img,
            )
        )
    print(f"Cantidad de bicicletas en la lista: {len(bicycles_list)}")
    return bicycles_list


# Recibe una lista de objetos Bicycle y crea un archivo json donde guardar toda la informacion de las bicicletas
def create_json(bicycles_list):
    with open("bicycles_db.json", "w", encoding="utf-8") as file:
        json.dump(
            [bicycle.to_dict() for bicycle in bicycles_list],
            file,
            ensure_ascii=False,
            indent=4,
        )


# Recibe la soup de una bicicleta y retorna su precio actual
def get_todays_price(bicycle):
    return [
        price.text.replace("\xa0", "")
        .replace("€", "")
        .replace(".", "")
        .replace(",", ".")
        for price in bicycle.find_all("span", class_="price")
    ][0]


# Busca en el archivo json cada bicicleta por su referencia y le añade el precio de hoy
# Funcion para ejecutar cada dia
def add_todays_price2():
    today = str(datetime.date(datetime.now()))
    with open("bicycles_db.json", "r") as file:
        json_file = json.load(file.buffer)
    for bicycle in json_file:
        response_search_reference = requests.get(
            urljoin(url, search_endpoint.format(bicycle["reference"]))
        )
        print(bicycle["reference"])
        if response_search_reference.status_code == 200:
            reference_soup = BeautifulSoup(
                response_search_reference.text, "html.parser"
            )
            if "La búsqueda no ha devuelto ningún resultado." in reference_soup.text:
                print(f"Reference {bicycle['reference']} was deleted")
                # Agregar funcion para eliminar la referencia del json
                continue
            else:
                todays_price = (
                    reference_soup.find_all("span", class_="price")[0]
                    .text.replace("\xa0", "")
                    .replace("€", "")
                    .replace(".", "")
                    .replace(",", ".")
                )

            bicycle["prices"][today] = float(todays_price)
    with open("bicycles_db.json", "w") as file:
        json.dump(json_file, file, indent=4, ensure_ascii="utf-8")


# Funcion para revisar si se ha cambiado el precio y en solo ese caso, agregarlo al json
# Funcion en desuso
"""
def review_prices_changes():
    changed_prices_bicycles = []
    with open("bicycles_db.json", "r") as file:
        file_json = json.load(file)
        for bicycle in file_json:
            response = requests.get(
                urljoin(url, search_endpoint.format(bicycle["reference"]))
            ).text
            if "La búsqueda no ha devuelto ningún resultado." not in response:
                pattern = r'<span class="price">(.*?)</span>'
                try:
                    price = re.findall(pattern, response)[0]
                except IndexError:
                    print("Search finished")
                clean_price = float(
                    price.replace("\xa0", "")
                    .replace("€", "")
                    .replace(".", "")
                    .replace(",", ".")
                )
                bicycle["prices"][str(datetime.date(datetime.now()))] = clean_price
                if bicycle["current_price"] != clean_price:
                    print(f"The {bicycle['name']} price has changed")
                    bicycle["current_price"] = clean_price
                    changed_prices_bicycles.append(bicycle)
            else:
                print(f"The reference {bicycle['reference']} was deleted")
                # Ejecutar funcion de eliminar bicicleta del json

        if len(changed_prices_bicycles) > 0:
            send_alert(changed_prices_bicycles)
        else:
            print("Any price changed")
        with open("bicycles_db.json", "w") as file:
            json.dump(file_json, file, indent=4, ensure_ascii="utf-8")

"""


# Funcion para enviar alerta por mail de cambio de precio
def send_alert(bicycles, to=os.getenv("EMAIL")):
    from_ = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")

    mail = MIMEMultipart()
    mail["From"] = from_
    mail["To"] = to
    mail["Subject"] = "Biking Alert"
    message = ""
    for bicycle in bicycles:
        message = message + (
            f"La {bicycle['name']} ha cambiado de precio!\n{bicycle['url']}\n\n"
        )
    mail.attach(MIMEText(message, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_, password)
        server.send_message(mail)


# Funcion para revisar si hay alguna bicicleta nueva
def search_new_bikes():
    usp_warn = False
    counter = 1
    while usp_warn == False:
        print(f"Get request page {counter}")
        try:
            response = requests.get(
                urljoin(bicycles_url, page_endpoint.format(counter))
            )
            if (
                "No podemos encontrar productos que coincida con la selección."
                in response.text
            ):
                usp_warn = True
            # Creamos la soup con BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")
            # Obtener el contenedor de cada bicicleta, crear cada Bycicle y guardar en una lista
            bicycles = soup.find_all("li", class_="item product product-item")
            for bicycle in bicycles:
                href = bicycle.find("a")["href"]
                try:
                    href_response = requests.get(href).text
                    pattern = r'itemprop="sku">(.*?)</div>'
                    reference = re.search(pattern, href_response).group(1)
                    # Buscar la referencia en el json
                    with open("bicycles_db.json", "r") as file:
                        file_json = str(json.load(file))
                        reference_pattern = rf"'reference': '{reference}'"
                        if not reference_pattern in file_json:
                            print("Adding new bike to json")
                            print(reference)
                            add_new_bike_to_json(reference)
                except:
                    print("Search end")
                    return
            counter += 1
        except:
            print("An error occurred")


def add_new_bike_to_json(reference):
    response = requests.get(urljoin(url, search_endpoint.format(reference))).text
    soup = BeautifulSoup(response, "html.parser")
    bicycle_img = soup.find("img", class_="product-image-photo")["src"]
    bicycle_href = soup.find("a", class_="product photo product-item-photo")["href"]
    response_href = requests.get(bicycle_href)
    if response_href.status_code == 200:
        bicycle_name = (
            BeautifulSoup(response_href.text, "html.parser")
            .find("span", itemprop="name")
            .text
        )
    print(bicycle_name)
    bicycle_price = float(get_todays_price(soup))
    new_bicycle = Bicycle2(
        bicycle_name, bicycle_price, bicycle_href, reference, bicycle_img
    )
    with open("bicycles_db.json", "r") as file:
        file_json = json.load(file)
        file_json.append(new_bicycle.to_dict())
        # print(new_bicycle.to_dict())
        with open("bicycles_db.json", "w") as file:
            json.dump(file_json, file)


# Crear funcion para eliminar las bicicletas que ya no esten publicadas (o quizas pasarlas a un registro a parte para no perder los datos)


# Funcion para generar una alerta si el precio bajo
def alert_lower_price(reference, today_price):
    with open("bicycles_db.json", "r") as file:
        file_json = json.load(file)
        for bicycle in file_json:
            if (
                bicycle["reference"] == str(reference)
                and float(bicycle["current_price"]) > today_price
            ):
                print(
                    f"La {bicycle['name']} (referencia {bicycle['reference']}) ha bajado de precio!!"
                )


# Funcion para mostrar en consola la evolucion de el precio de una bicicleta
def get_prices(name=None, reference=None):
    if name == None and reference == None:
        print("Se debe pasar un nombre o referencia")
        return
    with open("bicycles_db.json", "r") as file:
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


# Crea el grafico de todas las bicicletas den json
## Crear un endpoint que ejecute este codigo con la bicicleta que se quiere mostrar el grafico, para no tener todos los graficos en la base de datos de antemano
def prices_graph_ploty(reference):
    with open("bicycles_db.json", "r") as file:
        json_file = json.load(file)
    for bicycle in json_file:
        if bicycle["reference"] == reference:
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
            print(f"Prices graph: prices_html/price_{bicycle['reference']}.html")


def prices_graph_matplotlib(reference):
    with open("bicycles_db.json", "r") as file:
        json_file = json.load(file)
    reference_exist = False
    for bicycle in json_file:
        if bicycle["reference"] == reference:
            reference_exist = True
            dates = sorted(bicycle["prices"].keys())
            prices = [bicycle["prices"][date] for date in dates]

            plt.figure(figsize=(10, 5))
            plt.plot(dates, prices, marker="o", linestyle="-", color="blue")
            plt.title(f"Evolucion del precio - {bicycle['name']}")
            plt.xlabel("Fecha")
            plt.ylabel("Precio")
            plt.savefig(f"prices_png/prices_{bicycle['reference']}.png")
            print(
                f"You can see the prices graph of {bicycle['name']} here: prices_png/prices_{bicycle['reference']}.png"
            )
    print("Reference not exist") if not reference_exist else ""


# Ejecutar cada dia para que busque bicicletas nuevas, añada los precios de hoy, envie las alertas al mail de los clientes de cambios de precio
def exec_every_day():
    search_new_bikes()
    add_todays_price()


system("clear")

# add_todays_price()
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
# search_new_bikes()
# add_new_bike_to_json(28116)
# exe_app()
# send_subscript_confirm("prueba@gmail.com", 30480)
# exec_every_day()
