from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from bs4 import BeautifulSoup
import requests, os, dotenv
from urllib.parse import urljoin
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
from .forms import SubscriptionForm
from .task import create_bicycles_task
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

dotenv.load_dotenv()

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

@login_required
def signout(request):
    logout(request)
    return redirect("home")

def scraping(request):
    return render(request, "create_bicycles.html", {
        "cron_token": settings.CRON_SECRET_TOKEN
    })

@csrf_exempt
def extract_bicycles_from_web(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method"}, status=405)
    
    token = request.GET.get("token") or request.POST.get("token")
    if token != settings.CRON_SECRET_TOKEN:
        print(token)
        print(settings.CRON_SECRET_TOKEN)
        return JsonResponse({"error": "Not authorized"}, status=403)

    usp_warn = False
    counter = 1
    while not usp_warn:
        print(f"Get request page {counter}")
        response = requests.get(urljoin(bicycles_url, page_endpoint.format(counter)))
        if (
            "No podemos encontrar productos que coincida con la selección."
            in response.text
        ):
            usp_warn = True
            break
        # Creamos la soup con BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        # Obtener el contenedor de cada bicicleta, crear cada Bycicle y guardar en una lista
        bicycles = soup.find_all("li", class_="item product product-item")
        counter += 1
        try:
            create_bicycles_task.delay(bicycles)
        except ValueError:
            return render(request, "home.html", {"message": "Bicycle saving completed"})
    return render(request, "create_bicycles.html")

def extract_bicycles_from_web2(request):
    if request.method == "GET":
        return render(request, "create_bicycles.html")
    else:
        usp_warn = False
        counter = 1
        while not usp_warn:
            print(f"Get request page {counter}")
            response = requests.get(urljoin(bicycles_url, page_endpoint.format(counter)))
            if (
                "No podemos encontrar productos que coincida con la selección."
                in response.text
            ):
                usp_warn = True
                break
            # Creamos la soup con BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")
            # Obtener el contenedor de cada bicicleta, crear cada Bycicle y guardar en una lista
            bicycles = soup.find_all("li", class_="item product product-item")
            counter += 1
            try:
                create_bicycles_task.delay(bicycles)
            except ValueError:
                return render(request, "home.html", {"message": "Bicycle saving completed"})
        return render(request, "create_bicycles.html")



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

@login_required
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

@login_required
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

