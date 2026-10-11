from django.shortcuts import render

def scraping_page(request):
    return render(request, "scraping.html")

