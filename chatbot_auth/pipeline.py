# chatbot_auth/pipeline.py
import logging
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout
from social_django.models import UserSocialAuth

logger = logging.getLogger('chatbot_auth')

def catch_auth_already_associated(backend, uid, user=None, *args, **kwargs):
    """Handle social auth: allow sign-in, block conflicting sign-up."""
    logger.debug(f"Pipeline step called for backend: {backend}, uid: {uid}")
    request = kwargs.get('request')
    if not request:
        logger.warning("No request object in pipeline")
        return None

    # Check if the UID is already associated with a user
    try:
        existing_social = UserSocialAuth.objects.get(provider=backend.name, uid=uid)
        existing_user = existing_social.user
        logger.info(f"Found existing user: {existing_user.username}")

        # If a user is logged in and differs from the existing user
        if user and user != existing_user:
            logger.info(f"Conflict detected: Current user {user.username} differs from existing user {existing_user.username}")
            # Log out the current user to allow sign-in with the Google account
            logout(request)
            logger.debug("Logged out current user to proceed with Google login")
            return {
                'user': existing_user,  # Use the existing Google user
                'is_new': False
            }

        # If no user is logged in, proceed with existing user login
        if user is None:
            logger.debug("No user logged in; proceeding with existing user login")
            return {
                'user': existing_user,
                'is_new': False
            }

        # If the same user is logged in, proceed (no conflict)
        logger.debug("Same user logged in; proceeding")
        return None

    except UserSocialAuth.DoesNotExist:
        # No existing association, continue pipeline (new user sign-up)
        logger.debug("No existing association found; proceeding with new user")
        return None
    except Exception as e:
        logger.error(f"Error checking social auth: {e}")
        return None