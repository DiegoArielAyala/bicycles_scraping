from rest_framework.pagination import PageNumberPagination

class BicyclePagination(PageNumberPagination):
    page_size = 10

class SubscriptionsPagination(PageNumberPagination):
    page_size = 30