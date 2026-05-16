from rest_framework.generics import CreateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated

from ...models import Subscription
from ..serializers import SubscriptionSerializer, UnsubscribeSerializer

class SubscriptionView(CreateAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    queryset = Subscription.objects.all()

class UnsubscribeView(DestroyAPIView):
    serializer_class = UnsubscribeSerializer
    permission_classes = [IsAuthenticated]
    queryset = Subscription.objects.all()

    def destroy(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subscription = serializer.validated_data["subscription"]
        subscription.delete()

        return Response({"detail": "Unsubscribed successfully"})