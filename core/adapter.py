from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class NoDirectSignupAdapter(DefaultAccountAdapter):
    """Block all direct signups, but allow Google OAuth signups."""

    def is_open_for_signup(self, request):
        # 1. Allow if it's a social login (check for attribute)
        if hasattr(request, "sociallogin"):
            return True
            
        # 2. Robust check: Allow if the URL path contains 'google' or 'social'
        # This covers the callback phase where accounts are created.
        if "/accounts/google/" in request.path or "/social/" in request.path:
            return True

        # 3. Otherwise, block (this stops /accounts/signup/ and standard forms)
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
        """
        This method is called after the User object is saved to the DB.
        The post_save signal in models.py will have already created the Profile.
        """
        user = super().save_user(request, sociallogin, form)
        
        try:
            from core.models import Level
            # The profile is created by the post_save signal in models.py
            profile = user.profile
            
            # If the profile doesn't have a level assigned yet, give them Level 1
            if not profile.level:
                level_1 = Level.objects.filter(level_number=1).first()
                if level_1:
                    profile.level = level_1
            
            profile.role = "worker"
            profile.save()
        except Exception as e:
            # Log error if necessary, but don't crash the login flow
            print(f"Error updating profile in adapter: {e}")
            
        return user