import logging

from django.contrib.auth import login
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from ...models import Bicycle
from ..serializers import UserSerializer, BicycleSerializer, SigninSerializer

logger = logging.getLogger(__name__)

class SignupView(CreateAPIView):
    serializer_class = UserSerializer

class SearchBicycleView(ListAPIView):
    serializer_class = BicycleSerializer

    def get_queryset(self):
        max_results = 50
        qs = Bicycle.objects.all()
        query = (self.request.query_params.get("q") or "").strip()
        
        if not query:
            return qs[:max_results]

        if query.isdigit():
            qs = qs.filter(reference=query)
        else:
            qs = qs.filter(name__icontains=query)

        return qs.order_by("price")[:max_results]
    
class SigninView(APIView):
    def post(self, request):
        serializer = SigninSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        
        return Response({"refresh": str(refresh), "access": str(refresh.access_token)})
