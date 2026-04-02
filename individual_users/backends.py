from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailOrPhoneBackend(ModelBackend):
    """
    Authenticate individual users by email or phone number + password.
    Only matches users with user_type='individual'.
    """

    def authenticate(self, request, email=None, phone=None, password=None, **kwargs):
        # Skip if this is a normal username/password login (handled by default backend)
        if email is None and phone is None:
            return None

        user = None
        if email:
            try:
                user = User.objects.get(email__iexact=email, user_type='individual')
            except User.DoesNotExist:
                return None
        elif phone:
            try:
                from individual_users.models import IndividualProfile
                profile = IndividualProfile.objects.select_related('user').get(
                    phone_number=phone, user__user_type='individual',
                )
                user = profile.user
            except Exception:
                return None

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
