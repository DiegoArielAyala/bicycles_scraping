from rest_framework import status
from rest_framework.generics import CreateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ...models import Subscription
from ..serializers import SubscriptionSerializer, UnsubscribeSerializer

class SubscriptionView(CreateAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    queryset = Subscription.objects.all()

class UnsubscribeView(DestroyAPIView):
    serializer_class = UnsubscribeSerializer
    queryset = Subscription.objects.all()

    def destroy(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subscription = serializer.validated_data["subscription"]
        subscription.delete()

        return Response({"detail": "Unsubscribed successfully"})
    
class UnsubscribeByTokenView(APIView):
    def get(self, request, token):
        try:
            subscription = Subscription.objects.get(unsubscribe_token=token)
            subscription.delete()
            return Response({"detail": "Unsubscribed successfully"})
        except Subscription.DoesNotExist:
            return Response({"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)