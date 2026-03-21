# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Authentication ViewSet for API v1.

Handles login, logout, registration, and user information.

Made with love by Kartoza | https://kartoza.com
"""
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response

from bims.api.v1.responses import success_response, error_response


class AuthViewSet(ViewSet):
    """
    ViewSet for authentication operations.

    Provides endpoints for:
    - Login with username/password
    - Logout
    - Registration
    - Current user info
    - CSRF token
    """

    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    @action(detail=False, methods=["get"])
    def csrf(self, request):
        """Get CSRF token for forms."""
        return success_response(
            data={"csrfToken": get_token(request)},
            meta={"message": "CSRF token set in cookie"}
        )

    @action(detail=False, methods=["post"])
    def login(self, request):
        """
        Login with username and password.

        Returns user info on success.
        """
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return error_response(
                errors={"detail": "Username and password are required"},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return success_response(
                    data=self._serialize_user(user),
                    meta={"message": "Login successful"}
                )
            else:
                return error_response(
                    errors={"detail": "Account is disabled"},
                    status_code=status.HTTP_403_FORBIDDEN
                )
        else:
            return error_response(
                errors={"detail": "Invalid username or password"},
                status_code=status.HTTP_401_UNAUTHORIZED
            )

    @action(detail=False, methods=["post"])
    def logout(self, request):
        """Logout current user."""
        logout(request)
        return success_response(
            data=None,
            meta={"message": "Logout successful"}
        )

    @action(detail=False, methods=["post"])
    def register(self, request):
        """
        Register a new user.

        Required fields: username, email, password1, password2
        Optional fields: first_name, last_name
        """
        from django.contrib.auth import get_user_model
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError

        User = get_user_model()

        username = request.data.get("username", "").strip()
        email = request.data.get("email", "").strip()
        password1 = request.data.get("password1", "")
        password2 = request.data.get("password2", "")
        first_name = request.data.get("first_name", "").strip()
        last_name = request.data.get("last_name", "").strip()

        # Validation
        errors = {}

        if not username:
            errors["username"] = "Username is required"
        elif User.objects.filter(username=username).exists():
            errors["username"] = "Username is already taken"

        if not email:
            errors["email"] = "Email is required"
        elif User.objects.filter(email=email).exists():
            errors["email"] = "Email is already registered"

        if not password1:
            errors["password1"] = "Password is required"
        elif password1 != password2:
            errors["password2"] = "Passwords do not match"
        else:
            try:
                validate_password(password1)
            except ValidationError as e:
                errors["password1"] = list(e.messages)

        if errors:
            return error_response(
                errors=errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
            )

            # Auto-login after registration
            login(request, user)

            return success_response(
                data=self._serialize_user(user),
                meta={"message": "Registration successful"}
            )

        except Exception as e:
            return error_response(
                errors={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def user(self, request):
        """Get current authenticated user info."""
        return success_response(
            data=self._serialize_user(request.user)
        )

    @action(detail=False, methods=["patch"], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """Update current user's profile."""
        user = request.user

        if "first_name" in request.data:
            user.first_name = request.data["first_name"]
        if "last_name" in request.data:
            user.last_name = request.data["last_name"]
        if "email" in request.data:
            user.email = request.data["email"]

        user.save()

        return success_response(
            data=self._serialize_user(user),
            meta={"message": "Profile updated"}
        )

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Change current user's password."""
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError

        user = request.user
        current_password = request.data.get("current_password", "")
        new_password = request.data.get("new_password", "")
        confirm_password = request.data.get("confirm_password", "")

        if not user.check_password(current_password):
            return error_response(
                errors={"current_password": "Current password is incorrect"},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        if new_password != confirm_password:
            return error_response(
                errors={"confirm_password": "Passwords do not match"},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return error_response(
                errors={"new_password": list(e.messages)},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        # Re-login to update session
        login(request, user)

        return success_response(
            data=None,
            meta={"message": "Password changed successfully"}
        )

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def create_expert(self, request):
        """
        Create a new user to be added as an expert.

        This creates a user with a random password (they can reset it later).
        Only authenticated users with change_taxongroup permission can do this.

        Required fields: first_name, email
        Optional fields: last_name
        """
        from django.contrib.auth import get_user_model
        import uuid

        # Check permission
        if not request.user.has_perm('bims.change_taxongroup'):
            return error_response(
                errors={"detail": "You do not have permission to create experts"},
                status_code=status.HTTP_403_FORBIDDEN
            )

        User = get_user_model()

        first_name = request.data.get("first_name", "").strip()
        last_name = request.data.get("last_name", "").strip()
        email = request.data.get("email", "").strip()

        # Validation
        errors = {}

        if not first_name:
            errors["first_name"] = "First name is required"

        if not email:
            errors["email"] = "Email is required"
        elif User.objects.filter(email=email).exists():
            errors["email"] = "A user with this email already exists"

        if errors:
            return error_response(
                errors=errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Generate username from email
        base_username = email.split('@')[0].lower()
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Generate a random password (user can reset via email)
        random_password = str(uuid.uuid4())

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=random_password,
                first_name=first_name,
                last_name=last_name,
            )

            return success_response(
                data={
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "name": f"{first_name} {last_name}".strip(),
                },
                meta={"message": "Expert created successfully"}
            )

        except Exception as e:
            return error_response(
                errors={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _serialize_user(self, user):
        """Serialize user object."""
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "date_joined": user.date_joined.isoformat(),
            "profile_image": getattr(user, "profile_image", {}).get("url") if hasattr(user, "profile_image") else None,
        }
