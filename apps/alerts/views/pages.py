from django.shortcuts import render

def subscription_page(request):
    reference = request.GET.get("reference")
    return render(request, "subscription.html", {"reference": reference})

def unsubscription_page(request):
    return render(request, "unsubscription.html")

def my_subscriptions_page(request):
    return render(request, "my_subscriptions.html")