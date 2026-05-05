import asyncio 
import os
import dotenv
import json
import smtplib
import plotly.graph_objects as go
import logging


from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..serializers import UserSerializer

from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from ...models import Bicycle, PriceHistory, Subscription
from ...forms import SubscriptionForm
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from ...runner import run_scraper


dotenv.load_dotenv(".env." + os.getenv("ENV", "local"))
logger = logging.getLogger(__name__)

def home(request):
    return render(request, "home.html")

@api_view(["POST"])
def signup(request):
    logger.debug({"event": "signup"})
    serializer = UserSerializer(data=request.data)

    try:
        serializer.is_valid(raise_exception=True)
    except serializers.ValidationError as e:
        logger.warning({"event": "signup_validation_error", "errors": e.detail})
        return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.save()

    logger.info({"event": "user_created", "username": user.username})

    return Response(
        {"message": "User created successfully",
         "username": user.username}, 
         status=status.HTTP_201_CREATED
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


"""
Elimine el campo reference del modelo Subscription. Hay que adaptar las funciones subscription y unsubscription para que la reference la obtenga a traves de bicycle.reference, y no directamente reference.
"""
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

