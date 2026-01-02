from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from bs4 import BeautifulSoup
import os, dotenv
from urllib.parse import urljoin
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import plotly.graph_objects as go
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.db import IntegrityError
from .models import Bicycle, PriceHistory, Subscription
from .forms import SubscriptionForm
from .utils import create_bicycles
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth.stealth import Stealth
import asyncio, random
import re
from asgiref.sync import sync_to_async


dotenv.load_dotenv()

url = "https://www.bikingpoint.es/es/"
bicycles_endpoint = "bicicletas.html"
search_endpoint = "catalogsearch/result/?q={}"
page_endpoint = "?p={}"
bicycles_url = urljoin(url, bicycles_endpoint)

# Urls Escapa
url_escapa = "https://www.biciescapa.com/es/"
bicycles_endpoint_escapa = "bicicletas/?en-stock={}"

urls = {
    "escapa": {
        "bicycles_endpoint": "https://www.biciescapa.com/es/bicicletas/?en-stock=1&page={}",
        "web": "https://www.biciescapa.com/es/"
    },
    "biking_point": {
        "bicycles_endpoint": "https://www.bikingpoint.es/es/bicicletas.html/?p={}",
        "search_endpoint": "https://www.bikingpoint.es/es/catalogsearch/result/?q={}",
    }
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.183",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.198 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:112.0) Gecko/20100101 Firefox/112.0",
    "Mozilla/5.0 (Linux; Android 11; SM-A715F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
]


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
    return render(
        request, "create_bicycles.html", {"cron_token": settings.CRON_SECRET_TOKEN}
    )


@csrf_exempt
def extract_bicycles_from_web(request, start_page=1, last_page=30):
    print("Ejecutando extract_bicycles_from_web")
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method"}, status=405)

    token = request.GET.get("token") or request.POST.get("token")
    if token != settings.CRON_SECRET_TOKEN:
        return JsonResponse({"error": "Not authorized"}, status=403)

    start_page = (
        request.GET.get("start_page") or request.POST.get("start_page") or start_page
    )
    last_page = (
        request.GET.get("last_page") or request.POST.get("last_page") or last_page
    )

    start_page = int(start_page)
    last_page = int(last_page)

    asyncio.create_task(run_scraper(start_page, last_page))

    if "text/html" in request.headers.get("Accept", ""):
        messages.success(request, "Scraping started in background")
        return redirect("create_bicycles")

    return JsonResponse({"message": "Scraping started in background"})


async def run_scraper(start_page, last_page, web=None, delete=False):
    print("run_scraper function start")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        counter = int(start_page)

        # Array with all bicycles references in the DB for the current web
        bicycle_references = await sync_to_async(
            lambda: list(Bicycle.objects.filter(web=web).values_list("reference", flat=True,))
            )()

        while counter <= last_page:

            url = (urls[web]["bicycles_endpoint"]).format(counter)
            print(f"url: {url}")
            try:
                list_page = await browser.new_page(user_agent=random.choice(USER_AGENTS))
                
                stealth = Stealth()
                await stealth.apply_stealth_async(list_page)
                await asyncio.sleep(random.uniform(3, 6))
                await list_page.goto(url, wait_until="domcontentloaded")
                html = await list_page.content()
                soup = BeautifulSoup(html, "html.parser")
                print(f"soup: {soup.text[:200]}")
                try:
                    await list_page.wait_for_function("() => !document.body.innerText.includes('Verifying you are human')", timeout=60000)
                except e:
                    print(f"Error cloudflare challenge no se resolvio: {e}")

                html = await list_page.content()
                soup = BeautifulSoup(html, "html.parser")

                if web == "biking_point":
                    if (
                        "No podemos encontrar productos que coincida con la selección."
                        in soup.text
                    ):
                        print("No hay más productos, finalizando.")
                        break
                    else:
                        bicycles = soup.find_all("li", class_="item product product-item")
                        print(f"Página {counter}: Encontrados {len(bicycles)} bicicletas")
                
                if web == "escapa":
                    bicycles = soup.find_all("article", class_="product-miniature js-product-miniature mb-3")
                                
                # Call to create_bicycles and return an arrays with referencies that not exist yet in the DB
                bicycle_references = await create_bicycles(bicycles, USER_AGENTS, web, bicycle_references)
                print(f"new_bicycle_references: {bicycle_references}")
                
                counter += 1

                if web == "escapa":
                    search_number = (re.search(r"Mostrando \d+-(\d+)", soup.text)).group(1)
                    number_bicycles = (re.search(r"de (\d+) producto", soup.text)).group(1)
                    print(search_number)
                    print(number_bicycles)
                    if (number_bicycles == search_number):
                        print("No hay más productos, finalizando.")
                        break

            except Exception as e:
                print(f"Error en la página {counter}: {e}")
                break
        
        # Delete bicycles that no longer exists
        if delete:
            await delete_bicycles(bicycle_references)


        await browser.close()
    print("Scraping terminado.")


async def delete_bicycles(bicycles_reference):
    print("Deleting bicycles")
    for reference in bicycles_reference:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            try:
                page = await browser.new_page(user_agent=random.choice(USER_AGENTS))
                stealth = Stealth()
                await stealth.apply_stealth_async(page)
                await asyncio.sleep(random.uniform(3, 6))
                bicycle = await sync_to_async(lambda: get_object_or_404(Bicycle, reference=reference))()

                # Search reference on the corresponding page
                bicycle_exist = True
                if bicycle.web == "biking_point":
                    url = urls["biking_point"]["search_endpoint"]
                    await page.goto(url.format(reference))
                    content = await page.content()
                    if "La búsqueda no ha devuelto ningún resultado." in content:
                        bicycle_exist = False

                elif bicycle.web == "escapa":
                    url = urls["escapa"]["web"]
                    await page.goto(url)
                    try:
                        await page.click("button#onetrust-accept-btn-handler", timeout=3000)
                    except:
                        pass

                    await page.fill("input[name='s']", str(reference))
                    await asyncio.sleep(random.uniform(3, 6))
                    await page.wait_for_selector("div.dfd-card-flag", timeout=5000)

                    content = await page.content()
                    soup = BeautifulSoup(content, "html.parser")
                    try:
                        div = soup.find("div", class_="dfd-card-flag", attrs={"data-availability":"out-of-stock"})
                    
                        if div.text.strip() == "Agotado" or "Prueba de nuevo con otra búsqueda…" in soup.text:
                            bicycle_exist = False
                    except Exception as e:
                        print(f"Error finding bicycle in Escapa: {e}")

                # If bicycle not exist, delete it
                if not bicycle_exist:
                    await sync_to_async(bicycle.delete)()
                    print(f"Reference {reference} was deleted from web {bicycle.web}")

            except Exception as e:
                print("Error during delete bicycle: ", e)
            
            finally:
                await browser.close()


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
    bicycle = get_list_or_404(Bicycle, reference=reference)[0]
    price_history_list = get_list_or_404(PriceHistory, bicycle=bicycle.pk)

    dates = sorted([price.date for price in price_history_list])
    prices = []
    for date in dates:
        price_history = PriceHistory.objects.filter(bicycle=bicycle.pk, date=date)[0]
        prices.append(price_history.price)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=prices, mode="lines+markers", name="Precio"))
    fig.update_layout(
        plot_bgcolor="#212529",
        paper_bgcolor="#212529",
        title={
            "text": f"{bicycle.name}",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 24, "family": "system-ui"},
        },
        xaxis=dict(
            title=dict(text="Date", font=dict(color="#f8f9fa")),
            color="#f8f9fa",
            gridcolor="#343a40",
            linecolor="#f8f9fa",
            tickfont=dict(color="#f8f9fa"),
        ),
        yaxis=dict(
            title=dict(text="Price (€)", font=dict(color="#f8f9fa")),
            color="#f8f9fa",
            gridcolor="#343a40",
            linecolor="#f8f9fa",
            tickfont=dict(color="#f8f9fa"),
        ),
        hovermode="x unified",
        font=dict(
            family="system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
            size=16,
            color="#f8f9fa",
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
            return render(
                request, "subscription.html", {"form": form, "reference": reference}
            )
        except:
            return render(request, "subscription.html", {"form": form})
    else:
        bicycle = get_object_or_404(Bicycle, reference=request.POST["reference"])
        subscribe = Subscription(
            email=request.POST["email"],
            reference=request.POST["reference"],
            bicycle=bicycle,
        )
        try:
            subs_object = get_object_or_404(
                Subscription,
                email=request.POST["email"],
                reference=request.POST["reference"],
            )
            print(subs_object)
            return render(
                request,
                "subscription.html",
                {"form": form, "message": "Subscription already exist"},
            )
        except:
            subscribe.save()
            return render(
                request,
                "subscription.html",
                {"form": form, "message": "Subscribed successfully!"},
            )


@login_required
def unsubscription(request):
    form = SubscriptionForm()
    if request.method == "GET":
        return render(request, "unsubscription.html", {"form": form})
    else:
        subscription = get_object_or_404(
            Subscription,
            email=request.POST["email"],
            reference=request.POST["reference"],
        )
        # try:
        subscription.delete()
        return render(
            request,
            "unsubscription.html",
            {"form": form, "message": f"Unsubscribeb from {subscription.bicycle}"},
        )
        """
        except:
            return render(request, "unsubscription.html", {
                "form": form,
                "message": f"This subscription does not exist"
            })
        """


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

