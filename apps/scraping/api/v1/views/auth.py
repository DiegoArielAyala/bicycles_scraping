import jwt

from allauth.socialaccount.internal import jwtkit
from allauth.socialaccount.providers.google.views import (
    CERTS_URL,
    ID_TOKEN_ISSUER,
    GoogleOAuth2Adapter,
)
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from apps.scraping.api.v1.serializers import MeSerializer, UserSerializer, SigninSerializer, SignoutSerializer
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView


class ClockSkewGoogleOAuth2Adapter(GoogleOAuth2Adapter):
    """Allow WSL/local clock drift when validating Google's id_token iat/exp."""

    JWT_LEEWAY_SECONDS = 300

    def _decode_id_token(self, app, id_token):
        verify_signature = not self.did_fetch_access_token
        if verify_signature:
            alg, key = jwtkit.fetch_key(
                id_token,
                CERTS_URL,
                jwtkit.lookup_kid_pem_x509_certificate,
            )
            algorithms = [alg]
        else:
            key = ""
            algorithms = None

        data = jwt.decode(
            id_token,
            key=key,
            options={
                "verify_signature": verify_signature,
                "verify_iss": True,
                "verify_aud": True,
                "verify_exp": True,
            },
            issuer=ID_TOKEN_ISSUER,
            audience=app.client_id,
            algorithms=algorithms,
            leeway=self.JWT_LEEWAY_SECONDS,
        )
        jwtkit.verify_jti(data)
        return data


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
        
        return Response(status=status.HTTP_200_OK)


class GoogleLogin(SocialLoginView):
    adapter_class = ClockSkewGoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = settings.GOOGLE_OAUTH_CALLBACK_URL


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        serializer = MeSerializer(instance=user)
        return Response(serializer.data)