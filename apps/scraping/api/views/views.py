import os
import dotenv
import json
import smtplib
import logging


from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..serializers import UserSerializer

from django.shortcuts import render
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

