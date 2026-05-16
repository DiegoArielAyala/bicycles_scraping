from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

from ..serializers import UserSerializer, SigninSerializer, SignoutSerializer

class SignupView(CreateAPIView):
    serializer_class = UserSerializer

class SigninView(APIView):
    def post(self, request):
        serializer = SigninSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        
        return Response({"refresh": str(refresh), "access": str(refresh.access_token)})

class SignoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = SignoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh = serializer.validated_data["refresh"]
        refresh.blacklist()
        
        return Response({"message": "Successfully logged out"})
    
