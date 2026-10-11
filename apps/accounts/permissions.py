from django.conf import settings
from rest_framework.permissions import BasePermission

ROLE_USER = "user"
ROLE_MODERATOR = "moderator"
ROLE_ADMIN = "admin"


def get_user_roles(user) -> list[str]:
    if not getattr(user, "is_authenticated", False):
        return []

    roles = list(user.groups.values_list("name", flat=True))
    if user.is_staff or user.is_superuser:
        if ROLE_ADMIN not in roles:
            roles.append(ROLE_ADMIN)
    return roles


def user_has_role(user, role: str) -> bool:
    return role in get_user_roles(user)


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return user_has_role(request.user, ROLE_ADMIN)


class IsModeratorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return user_has_role(request.user, ROLE_MODERATOR) or user_has_role(
            request.user, ROLE_ADMIN
        )


class IsOwnerOrModerator(BasePermission):
    def has_object_permission(self, request, view, obj):
        if user_has_role(request.user, ROLE_MODERATOR) or user_has_role(
            request.user, ROLE_ADMIN
        ):
            return True
        return getattr(obj, "user", None) == request.user


class IsAdminOrCronService(BasePermission):
    def has_permission(self, request, view):
        cron_token = request.headers.get("X-CRON-TOKEN")
        if cron_token and cron_token == settings.CRON_SECRET_TOKEN:
            return True
        return user_has_role(request.user, ROLE_ADMIN)
