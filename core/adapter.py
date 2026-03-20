from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class NoDirectSignupAdapter(DefaultAccountAdapter):
    """Block all direct (username/password) signups — Google only."""

    def is_open_for_signup(self, request):
        return False


class GoogleSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    After Google OAuth creates a user:
      - auto-generate a unique username from their email
      - ensure a worker profile with Level 1 exists
    """

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        # Auto-generate username from Google email so the field is never blank
        if not user.username:
            from django.contrib.auth.models import User

            base = (data.get("email") or "user").split("@")[0]
            # Strip characters Django doesn't allow in usernames
            base = "".join(c for c in base if c.isalnum() or c in "_.-")[:28] or "user"
            candidate, n = base, 1
            while User.objects.filter(username=candidate).exists():
                candidate = f"{base}{n}"
                n += 1
            user.username = candidate
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        # Guarantee a Level-1 worker profile exists after first Google login
        try:
            from core.models import Level

            profile = user.profile
            if not profile.level:
                level_1 = Level.objects.filter(level_number=1).first()
                profile.level = level_1
            profile.role = "worker"
            profile.save()
        except Exception:
            pass
        return user