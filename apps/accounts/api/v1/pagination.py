from rest_framework.pagination import PageNumberPagination

class SubscriptionsPagination(PageNumberPagination):
    page_size = 30