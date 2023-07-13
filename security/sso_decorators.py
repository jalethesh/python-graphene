from flask import Blueprint, session

from flask import redirect, jsonify
import os


user_factory = Blueprint("user", __name__, static_folder="static", template_folder="templates")

USERINFO_URL = "https://purplemana.com/oauth/me"
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TOKEN_URL = "https://purplemana.com/oauth/token"
AUTHORIZATION_BASE_URL = "https://purplemana.com/oauth/authorize"


# login required decorator
def user_is_logged_in(func):
    def check_user_id(*args, **kwargs):
        if "user_id" not in session:
            print("user is not logged in, redirecting")
            raise Exception("user is not logged in, access denied")
        else:
            print("user is logged in or admin")
        return func(*args, **kwargs)
    # rename this function to the endpoint so that there aren't name collisions
    check_user_id.__name__ = func.__name__
    return check_user_id


# checks if user has admin role
def user_is_admin(func):
    def check_role_for_admin(*args, **kwargs):
        if 'roles' not in session or "administrator" not in session['roles']:
            print("user is not admin, access denied")
            raise Exception("user is not admin, access denied")
        else:
            print("user is admin")
            return func(*args, **kwargs)
    # rename this function to the endpoint so that there aren't name collisions
    check_role_for_admin.__name__ = func.__name__
    return check_role_for_admin


# clear email/roles in session for endpoints with this decorator
# def clear_session(func):
#     def drop_details():
#         if "email" in session:
#             del session['email']
#         if "roles" in session:
#             del session['roles']
#         return func()
#     return drop_details


