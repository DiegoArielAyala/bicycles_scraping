from django.contrib.auth.models import Group, User
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from apps.scraping.models import Bicycle, Subscription

class SignupAssignRolesTest(APITestCase):
    def setUp(self):
        self.user_group = Group.objects.get_or_create(name="user")

    def test_assign_user(self):
        response = self.client.post("/api/v1/signup/", {"username": "user_test", "password1": "passwordtest1!", "password2": "passwordtest1!"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username="user_test")

        self.assertTrue(user.groups.filter(name="user").exists())


class GuestCantSubscribeTest(APITestCase):
    def test_anonymous_cannot_create_subscription(self):
        response = self.client.post("/api/v1/subscription/", {"email": "test@mail.com", "reference": "11111"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Subscription.objects.count(), 0)

class SubscriptionPermissionsTests(APITestCase):
    def setUp(self):
        user = User.objects.create_user(username="user_test", password="passwordtest1!")
        self.user = user

        self.client.force_authenticate(user=user)

        Group.objects.get_or_create(name="user")
        Bicycle.objects.create(reference="11111", current_price=1000, name="bicycle_test")

    def test_user_can_create_subscription(self):
        response = self.client.post("/api/v1/subscription/", {"email": "test@mail.com", "reference": "11111"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        subscription = Subscription.objects.get(email="test@mail.com", bicycle=response.data["bicycle"])

        self.assertEqual(subscription.user == self.user, True)

    def test_user_cannot_delete_another_users_subscription(self):
        response = self.client.post("/api/v1/subscription/", {"email": "test@mail.com", "reference": "11111"}, format="json")
        subscription = response.data

        self.assertEqual(Subscription.objects.filter(email="test@mail.com", bicycle=subscription["bicycle"]).exists(), True)

        other_user = User.objects.create_user(username="user_test2", password="passwordtest1!")

        self.client.force_authenticate(user=other_user)

        response = self.client.delete("/api/v1/unsubscription/", {"email":"test@mail.com", "reference": "11111"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Subscription.objects.filter(email="test@mail.com", user=self.user.id).exists(), True)

class AdminSubscriptionsPermissionTests(APITestCase):
    def setUp(self):
        moderator = User.objects.create_user(username="moderator", password="passwordtest1!")
        user = User.objects.create_user(username="user", password="passwordtest1!")
        moderator_group = Group.objects.get(name="moderator")
        moderator.groups.add(moderator_group)
        self.moderator = moderator
        self.client.force_authenticate(user=user)
        references = ["11111", "22222"]
        for reference in references:
            Bicycle.objects.create(reference=reference, name="Bicycle_test", current_price=1000)
            self.client.post("/api/v1/subscription/", {"email": "test@mail.com", "reference": reference}, format="json")

    def test_moderator_can_list_all_subscriptions(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.get("/api/v1/admin/subscriptions/", format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

class ScrapingPermissionsTests(APITestCase):
    def setUp(self):
        moderator = User.objects.create_user(username="moderator", password="test1!")
        group_moderator = Group.objects.get(name="moderator")
        moderator.groups.add(group_moderator)
        self.moderator = moderator
        
        admin = User.objects.create_user(username="admin", password="test1!")
        group_admin = Group.objects.get(name="admin")
        admin.groups.add(group_admin)
        self.admin = admin

    @patch("apps.scraping.api.v1.views.scraping.trigger_github_action")
    def test_moderator_cannot_start_scraping(self, mock_trigger):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.post("/api/v1/scraping/", {"start_page": 1, "last_page": 2, "web": "test_web", "delete": False}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_trigger.assert_not_called()

    @patch("apps.scraping.api.v1.views.scraping.trigger_github_action")
    def test_admin_can_scraping_with_jwt(self, mock_trigger):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/v1/scraping/", {"start_page": 1, "last_page": 2, "web": "test_web", "delete": False}, format="json")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_trigger.assert_called_once()
    
    @override_settings(CRON_SECRET_TOKEN="cron-token-test")
    @patch("apps.scraping.api.v1.views.scraping.trigger_github_action")
    def test_valid_cron_token_can_scraping(self, mock_trigger):
        response = self.client.post("/api/v1/scraping/", {"start_page": 1, "last_page": 2, "web": "test_web", "delete": False}, format="json", HTTP_X_CRON_TOKEN="cron-token-test",)

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_trigger.assert_called_once()

class MeReturnsRolesTests(APITestCase):
    def setUp(self):
        self.cases = []
        for role_name in ("user", "moderator", "admin"):
            user = User.objects.create_user(
                username=f"{role_name}_me_test",
                password="test1!",
            )
            group = Group.objects.get(name=role_name)
            user.groups.add(group)
            self.cases.append((user, role_name))

    def test_me_returns_correct_roles_for_each_group(self):
        for user, expected_role in self.cases:
            with self.subTest(role=expected_role):
                self.client.force_authenticate(user=user)
                response = self.client.get("/api/v1/me/")

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertIn(expected_role, response.data["roles"])
                self.assertEqual(response.data["username"], user.username)