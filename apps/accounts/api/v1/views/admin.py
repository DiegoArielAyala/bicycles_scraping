from django.contrib.auth import get_user_model
from rest_framework.generics import ListAPIView

from apps.accounts.api.v1.pagination import SubscriptionsPagination
from apps.accounts.api.v1.serializers import AdminSubscriptionsSerializer, AdminUsersSerializer
from apps.alerts.models import Subscription
from apps.accounts.permissions import IsAdminRole, IsModeratorOrAdmin

User = get_user_model()

class AdminSubscriptionsView(ListAPIView):
    permission_classes = [IsModeratorOrAdmin]
    serializer_class = AdminSubscriptionsSerializer
    pagination_class = SubscriptionsPagination
    queryset = Subscription.objects.select_related("bicycle", "user").order_by("-created_at")

class AdminUsersView(ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminUsersSerializer
    queryset = User.objects.prefetch_related("groups")
