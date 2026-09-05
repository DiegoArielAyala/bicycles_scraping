from apps.scraping.api.v1.serializers import (
    MySubscriptionSerializer,
    SubscriptionSerializer,
    UnsubscribeSerializer,
)
from apps.scraping.models import Subscription
from apps.scraping.permissions import IsOwnerOrModerator
from rest_framework import status
from rest_framework.generics import DestroyAPIView, ListCreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class SubscriptionView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user).select_related(
            "bicycle"
        )

    def get_serializer_class(self):
        if self.request.method == "GET":
            return MySubscriptionSerializer
        return SubscriptionSerializer


class UnsubscribeView(DestroyAPIView):
    serializer_class = UnsubscribeSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrModerator]
    queryset = Subscription.objects.all()

    def destroy(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subscription = serializer.validated_data["subscription"]
        self.check_object_permissions(request, subscription)
        subscription.delete()
        return Response({"detail": "Unsubscribed successfully"})


class UnsubscribeByTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            subscription = Subscription.objects.get(unsubscribe_token=token)
            subscription.delete()
            return Response({"detail": "Unsubscribed successfully"}, status=status.HTTP_200_OK)
        except Subscription.DoesNotExist:
            return Response({"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)