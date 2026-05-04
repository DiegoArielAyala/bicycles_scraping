from rest_framework.generics import CreateAPIView

from ..serializers import UserSerializer

class SignupView(CreateAPIView):
    serializer_class = UserSerializer

    