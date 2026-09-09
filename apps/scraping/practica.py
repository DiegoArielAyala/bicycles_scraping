"""
def args(*argumentos):
    print(argumentos)

args(1, 2)

def kwargs(**clave_valor):
    print(clave_valor)

dict = {
    "nombre": "Diego"
}

kwargs(**dict)

def funcion_superior(funcion, parametro):
    return (funcion(parametro))

def duplicar(numero):
    print(numero*2)

funcion_superior(duplicar, 10)

numbers = [1, 2, 3]

resultado = tuple(map(lambda x: x * 2, numbers))

print(resultado)
resultado = list(x * 2 for x in numbers)
print(resultado)

x = 2
y = 3
result = (lambda x, y: x + y )(x, y)

print(result)

def decorador(func):
    def wrapper(*args, **kwargs):
        print("Antes")
        return func(*args, **kwargs)
    return wrapper

@decorador
def sumar(x, y):
    return x + y

print(sumar(x, y))

def generador_num():
    yield 1
    yield 2
    yield 3

gen = generador_num()

print(list(gen))
print(next(gen))
print(next(gen))
print(next(gen))
"""
import os
import sys
from pathlib import Path

from django.db.models import F, Avg, Case, CharField, Count, Exists, Max, OuterRef, Subquery, Value, When
from django.db.models.functions import Coalesce


BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()
from apps.scraping.models import Bicycle, PriceHistory
"""
print(list(Bicycle.objects.values_list("current_price", flat=True)[:10]))
print(Bicycle.objects.values("web").distinct())
print(Bicycle.objects.filter(current_price__lte = 1000)[:5])
print(list(Bicycle.objects.values_list("name")[:10]))
print(PriceHistory.bicycle)

print(list(Bicycle.objects.all()[:5]))
"""

"""
Genera una consulta por cada bicicleta
bicycles = Bicycle.objects.all()[:5]

for bike in bicycles:
    print(bike.price_history.all())

histories = PriceHistory.objects.select_related("bicycle")[:1]

for history in histories:
    print(history.bicycle.name)
    print(history.bicycle.current_price)
    print(history.date)
    print(history.price)
"""

"""
bicycles = Bicycle.objects.prefetch_related()[:5]

for bicycle in bicycles:
    print(bicycle.price_history.all()[:3])
    print(bicycle.name)

price: 3000
bicycle: scott

bicycles = Bicycle.objects.prefetch_related("price_history")[:2]

for bike in bicycles:
    price = bike.price_history.all()[:1]
    print(bike.name, price[0].price)

bicycles = PriceHistory.objects.values("bicycle").annotate(total=Count("id"), average = Avg("price"), max=Max("price"))[:3]

print(list(bicycles))

average = PriceHistory.objects.aggregate(average=Avg("price"))

print(average)

results = Bicycle.objects.values("current_price").annotate(average=Avg("current_price")).filter(current_price__gte=3000)[:3]
print(results)

"Bicicletas con menor precio actual que el promedio"

bicycles = Bicycle.objects.annotate(average_price=Avg("price_history__price")).filter(current_price__lt=F("average_price")).values("current_price", "average_price")[:3]


print(bicycles)


price_history_exists = PriceHistory.objects.filter(bicycle_id=OuterRef("id"))

bicycles = Bicycle.objects.filter(Exists(price_history_exists))

print(bicycles[:3])

prices = Bicycle.objects.annotate(price=Coalesce("current_price", 0))


categories = Bicycle.objects.annotate(
    category=Case(
        When(current_price__lt=2000,then=Value("Barata")), 
        When(current_price__lt=4000, then=Value("Media")),
        default=Value("Cara"),
        output_field=CharField(),
        )
    ).values_list("name","category")

print(categories)


prices = PriceHistory.objects.select_related("bicycle")[:3]
values = PriceHistory.objects.values_list()[:3]
bicycles = Bicycle.objects.prefetch_related("price_history")[:3]

for bicycle in bicycles:
    print(bicycle.values())
"""

references = ["80050", "59165", "80053"]

bicycles = Bicycle.objects.filter(reference__in=references)
print(bicycles)

bicycle = bicycles.filter(reference="80050").first()
print(bicycle.name)