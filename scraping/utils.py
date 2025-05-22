import requests
from .views import urljoin
from bs4 import BeautifulSoup
from .forms import BicycleForm
from django.shortcuts import get_object_or_404
from datetime import datetime
from .models import Bicycle, PriceHistory

url = "https://www.bikingpoint.es/es/"
search_endpoint = "catalogsearch/result/?q={}"


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
                try:
                    price_history = PriceHistory(
                        bicycle=new_bicycle,
                        date=datetime.now().date(),
                        price=bicycle_price,
                    )
                    price_history.save()
                except:
                    print("Error creating price_history")


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
                bicycle.current_price = float(todays_price)
                bicycle.save()
                print(
                    f"{bicycle.reference} changed price from {bicycle.current_price} to {todays_price}"
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