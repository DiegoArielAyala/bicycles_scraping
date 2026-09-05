from rest_framework.generics import ListAPIView

from apps.scraping.api.v1.pagination import SubscriptionsPagination
from apps.scraping.api.v1.serializers import AdminSubscriptionsSerializer, AdminUsersSerializer
from apps.scraping.models import Subscription, User
from apps.scraping.permissions import IsAdminRole, IsModeratorOrAdmin

class AdminSubscriptionsView(ListAPIView):
    permission_classes = [IsModeratorOrAdmin]
    serializer_class = AdminSubscriptionsSerializer
    pagination_class = SubscriptionsPagination
    queryset = Subscription.objects.select_related("bicycle", "user").order_by("-created_at")

class AdminUsersView(ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminUsersSerializer
    queryset = User.objects.prefetch_related("groups")
