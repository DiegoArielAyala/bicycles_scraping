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
import plotly.graph_objects as go
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.db import IntegrityError
from .models import Bicycle, PriceHistory, Subscription
from .forms import BicycleForm, SubscriptionForm

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
                bicycle_object = get_object_or_404(Bicycle, reference=bicycle_reference)
                print(f"Referencia {bicycle_reference} ya existe en la base de datos")
                print(bicycle_object.reference)
                add_todays_price(bicycle_object)
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
    if request.method == "GET":
        return render(request, "create_bicycles.html")
    else:
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
                return render(request, "home.html", {"message": "Bicycle saving completed"})
            except ValueError:
                return render(request, "home.html", {"error": "Bicycle saving completed"})
        return render(request, "create_bicycles.html")


def add_todays_price(bicycle):
    print(f"Adding todays price for {bicycle.reference}")
    response_search_reference = requests.get(
        urljoin(url, search_endpoint.format(bicycle.reference))
    )
    if response_search_reference.status_code == 200:
        reference_soup = BeautifulSoup(response_search_reference.text, "html.parser")
        if "La búsqueda no ha devuelto ningún resultado." in reference_soup.text:
            print(f"Reference {bicycle.reference} was deleted")
            bicycle.delete()
        else:
            todays_price = (
                reference_soup.find_all("span", class_="price")[0]
                .text.replace("\xa0", "")
                .replace("€", "")
                .replace(".", "")
                .replace(",", ".")
            )
            new_price_history = PriceHistory(
                bicycle=bicycle, date=datetime.now().date(), price=todays_price
            )
            new_price_history.save()
            if bicycle.current_price != float(todays_price):
                print(
                    f"{bicycle.reference} changed price from {bicycle.current_price} to {todays_price}"
                )


def prueba():
    bicycle = get_object_or_404(Bicycle, reference=34687)
    print(type(bicycle.current_price))
    response_search_reference = requests.get(
        urljoin(url, search_endpoint.format(bicycle.reference))
    )
    if response_search_reference.status_code == 200:
        reference_soup = BeautifulSoup(response_search_reference.text, "html.parser")
        if "La búsqueda no ha devuelto ningún resultado." in reference_soup.text:
            print(f"Reference {bicycle.reference} was deleted")
            bicycle.delete()
        else:
            todays_price = (
                reference_soup.find_all("span", class_="price")[0]
                .text.replace("\xa0", "")
                .replace("€", "")
                .replace(".", "")
                .replace(",", ".")
            )
            print(type(todays_price))
            print(bicycle.current_price == float(todays_price))



def search_bicycle(request, query=None):
    if request.method == "GET":
        return render(request, "search_bicycle.html")
    else:
        query = request.POST["query"]
        try:
            reference = int(query)
            if len(query) == 5:
                results = Bicycle.objects.filter(reference=reference)
            else:
                results = Bicycle.objects.filter(name__icontains=query)
        except:
            results = Bicycle.objects.filter(name__icontains=query)
        return render(request, "search_bicycle.html", {"results": results})


def get_price_history(request, reference):
    bicycle = get_object_or_404(Bicycle, reference=reference)
    price_history_list = get_list_or_404(PriceHistory, bicycle=bicycle.pk)

    dates = sorted([price.date for price in price_history_list])
    prices = []
    for date in dates:
        price_history = PriceHistory.objects.filter(bicycle=bicycle.pk, date=date)[0]
        prices.append(price_history.price)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=prices, mode="lines+markers", name="Precio"))
    fig.update_layout(
        title={
            "text": f"{bicycle.name} price history",
            "x":0.5,
            "xanchor": "center",
            "font": {"size": 24, "family": "system-ui"}
        },
        xaxis_title="Date",
        yaxis_title="Price (€)",
        hovermode="x unified",
        font=dict(
            family="system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
            size=16,
            color= "#212529",
        ),
        margin=dict(t=100, b=40, l=40, r=20),
    )
    graphic = fig.to_html()

    return render(request, "price_history.html", {"graphic": graphic})


def subscription(request):
    form = SubscriptionForm()
    if request.method == "GET":
        try:
            reference = request.GET.get("reference")
            form = SubscriptionForm(initial={"reference": reference})
            return render(request, "subscription.html", {
                "form": form
            })
        except:
            return render(request, "subscription.html", {
                "form": form
            })
    else:
        bicycle = get_object_or_404(Bicycle, reference=request.POST["reference"])
        subscribe = Subscription(email=request.POST["email"], reference=request.POST["reference"], bicycle=bicycle)
        try:
            subs_object = get_object_or_404(Subscription, email = request.POST["email"], reference=request.POST["reference"])
            print(subs_object)
            return render(request, "subscription.html", {
                "form": form,
                "message": "Subscription already exist"
            })
        except:
            subscribe.save()
            return render(request, "subscription.html", {
                "form": form,
                "message": "Subscribed successfully!"
            })

def unsubscription(request):
    form = SubscriptionForm()
    if request.method == "GET":
        return render(request, "unsubscription.html", {
            "form": form
        })
    else:
        subscription = get_object_or_404(Subscription, email=request.POST["email"], reference=request.POST["reference"])
        # try:
        subscription.delete()
        return render(request, "unsubscription.html", {
            "form": form,
            "message": f"Unsubscribeb from {subscription.bicycle}"
        })
        """
        except:
            return render(request, "unsubscription.html", {
                "form": form,
                "message": f"This subscription does not exist"
            })
        """



# system("clear")
# get_price_history(34687)





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



# Recibe la soup de una bicicleta y retorna su precio actual
def get_todays_price(bicycle):
    return [
        price.text.replace("\xa0", "")
        .replace("€", "")
        .replace(".", "")
        .replace(",", ".")
        for price in bicycle.find_all("span", class_="price")
    ][0]


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
def get_prices2(name=None, reference=None):
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


# Ejecutar cada dia para que busque bicicletas nuevas, añada los precios de hoy, envie las alertas al mail de los clientes de cambios de precio
def exec_every_day():
    search_new_bikes()
    add_todays_price()


# system("clear")

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
