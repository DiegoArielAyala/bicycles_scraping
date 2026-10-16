from django.urls import path, include

from apps.accounts.api.v1.views import auth, admin


urlpatterns = [
    path("signin/", auth.SigninView.as_view(), name="signin_api"),
    path("signup/", auth.SignupView.as_view(), name="signup_api"),
    path("signout/", auth.SignoutView.as_view(), name="signout_api"),
    path("auth/", include("dj_rest_auth.urls")),
    path("auth/registration/", include("dj_rest_auth.registration.urls")),
    path("auth/google/", auth.GoogleLogin.as_view(), name="google_signin_api"),
    path("me/", auth.MeView.as_view(), name="me_api"),
    path("admin/subscriptions/", admin.AdminSubscriptionsView.as_view(), name="admin_subscriptions_api"),
    path("admin/users/", admin.AdminUsersView.as_view(), name="admin_users_api")
]