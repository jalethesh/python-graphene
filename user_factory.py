from datetime import datetime
from attr import attr, attrib
from flask import Blueprint, session
from sqlalchemy import or_

from models.data_models import db, Users, ItemCollections
import requests
from flask import jsonify, request, redirect, make_response
import os
import json
from security import user_is_admin, user_is_logged_in
import time
import boto3
import random

user_factory = Blueprint("user", __name__, static_folder="static", template_folder="templates")

USERINFO_URL = "https://purplemana.com/oauth/me"
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TOKEN_URL = "https://purplemana.com/oauth/token"
AUTHORIZATION_BASE_URL = "https://purplemana.com/oauth/authorize"
FLASK_URI = os.getenv('FLASK_URI')
RETURN_URL = FLASK_URI

COGNITO_AUTHORIZATION_URL = "https://auth.purplemana.com/login"
AWS_COGNITO_TOKEN_URL = "https://auth.purplemana.com/oauth2/token"
REDIRECT_URI = f"{FLASK_URI}/callback"
COGNITO_CLIENT_ID = "7ppduvj2a7kv27atmf23jc0u4"
COGNITO_CLIENT_SECRET = os.getenv("AWS_COGNITO_CLIENT_SECRET")
COGNITO_USERPOOL_ID = os.getenv("AWS_COGNITO_USERPOOL_ID")


# the front end will send a request to this endpoint to start sso
# user is redirected to purplemana login page, which will redirect on success to the provided url in return_url
# first time users will be registered in the database by successfully logging in through the purplemana redirect
@user_factory.route("/login")
def login():
    query_params = {
        "client_id": CLIENT_ID,
        "redirect_uri": f"{FLASK_URI}/users/register",
        "response_type": "code",
        "scope": "basic",
    }  
    return_url = request.args.get("return_url")
    session['return_url'] = return_url
    res = requests.get(AUTHORIZATION_BASE_URL, params=query_params)
    print(return_url)
    return redirect(res.url)


@user_factory.route("/cognito")
def login_cognito():
    query_params = {
        "client_id": COGNITO_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code", 
    }
    return_url = RETURN_URL
    if request.args.get("return_url"):
        return_url = request.args.get("return_url")
    
    session['return_url'] = return_url
    print(session['return_url'])
    res = requests.get(COGNITO_AUTHORIZATION_URL, params=query_params)
    return redirect(res.url)


@user_factory.route("/callback")
def callback_cognito():
    start = time.perf_counter()

    code = request.args.get('code')
    if not code:
        return jsonify({"message" : "Missing argument code"})

    params = {
        "grant_type": "authorization_code",
        "code": request.args.get('code'),
        "client_id": COGNITO_CLIENT_ID,
        "client_secret": COGNITO_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI
    }
    auth = requests.auth.HTTPBasicAuth(COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET)
    response = requests.post(AWS_COGNITO_TOKEN_URL, auth=auth, data=params).json()

    if not {'id_token', 'access_token', 'refresh_token'}.issubset(response.keys()):
        return jsonify({"message": f"error: missing id, access or refresh token, this is most likely caused by invalid code"})
    
    id_token, access_token, refresh_token = response['id_token'], response['access_token'], response['refresh_token']
    client = boto3.client('cognito-idp', region_name="us-east-1")
    res = client.get_user(
        AccessToken=access_token
    )
    try:
        parsed_response = parse_sso_response_data(res)
        user_email, cognito_id = handle_session_assignment(access_token, parsed_response)
        print(f"Email, cognito id: {user_email}, {cognito_id}")
        # either user was new and created, or exists already
        # retrieve user from DB and set cookie using data from DB
        user = db.session.query(Users).filter(or_(Users.email == user_email, Users.cognito_id == cognito_id)).first()
        try:
            session['user_id'] = user.database_id
        except Exception as ex:
            print(f"{'|' * 20} user was created, but error retrieving from database")
        try:
            user.last_login = datetime.now()
            db.session.add(user)
            db.session.commit()
        except Exception as ex:
            print(f"{'-' * 20} unable to set last login for user")
        try:
            default = db.session.query(ItemCollections).filter_by(user_id=session['user_id'], name='default').first()
            if not default:
                default = ItemCollections(user_id=session['user_id'], name='default')
                db.session.add(default)
                db.session.commit()
        except Exception as ex:
            print("unable to locate or create a default collection for", session["user_id"])
        # For some reason
        if 'return_url' not in session:
            session['return_url'] = RETURN_URL

        response = make_response(redirect(session['return_url']))
        user_data = {'email' : session['email'], 'nicename' : session['username'], 'id' : session['user_id'], 'role' : session['roles']}
        session['userInfo'] = user_data
        print("Session:", session)

        end = time.perf_counter()
        print(f"Time mesured: {end - start} seconds")
        return response

    except Exception as ex:
        print(str(ex))
        return jsonify({"error": "some exception during login"})


def handle_session_assignment(access_token, parsed_response):
    """ Seperate function, which is part of the user auth used in callback """

    print("-" * 10, "Parsed response:", "-" * 10, parsed_response)
    providers = ["Google", "Facebook"]
    user_email = ''
    cognito_id = ''
    # If the auth is conducted through sso
    if 'providerName' in parsed_response.keys() and parsed_response['providerName'] in providers:
        try:
            parsed_response['Username'] = parsed_response['given_name'] + parsed_response['family_name'][0]
        except Exception as ex:
            print(ex)
        cognito_id = parsed_response['userId']
    else:
        cognito_id = None # random.randint(10 ** 20, 1.2 * 10 ** 20)

    user_email = parsed_response['email']
    session['username'] = parsed_response['Username']
    session['email'] = user_email
    session['roles'] = ['guest']
    # session['ID'] = parsed_response['sub']  sub value
    session['expiration'] = time.time() + 3600
    role = "administrator" if "administrator" in session['roles'] else "guest"
    user = Users(username=parsed_response['Username'], security_role=role, date_created=datetime.now(), email=user_email, cognito_id=cognito_id)

    print("user", user, cognito_id, user.email)
    new_user = True
    try:
        if cognito_id:
            result = db.session.query(Users).filter(Users.cognito_id == cognito_id).first()
        else:
            result = db.session.query(Users).filter(Users.email == user_email).first()
        if result:
            user = result
            print("result", result, "|", f"{Users.email} == {user_email} ### {Users.cognito_id} == {cognito_id} | {Users.cognito_id == 'cognito_id'}")
            new_user = False
            session['roles'] = [user.security_role]
            session['username'] = user.username
            user.cognito_id = cognito_id
    except Exception as ex:
        print("#", ex)

    try:
        user.token = access_token
        user.expiration = int(time.time()) + 3600
        print("Is new user:", new_user)
        if new_user:
            db.session.add(user)
        db.session.commit()
    except Exception as ex:
        return jsonify({"message": f"error creating user in database {ex}"})

    # check for email and update if necessary
    try:
        assert user.email
        assert user.email != ''
    except:
        try:
            # if there is user with different id and same Users.email and user_email
            user_with_that_email = db.session.query(Users).filter(Users.email == user_email).first()
            user.email = user_email
            db.session.add(user)
            db.session.commit()
        except Exception as ex:
            print("#" * 5, "user with same email already exists", ex)

    return user_email, cognito_id

def parse_sso_response_data(response):
    """This function formats nested response data into an one layer dictonary """
    result = {}
    for key_name in response:
        if key_name == 'Username':
            result.update({key_name : response[key_name]})

        elif key_name == 'UserAttributes':
            attributes = {v['Name'] : v['Value'] for v in response[key_name]}
            for attribute in attributes:
                if attribute == "identities":
                    result.update({key : value for key, value in json.loads(attributes[attribute])[0].items()})
                else:
                    result.update({attribute : attributes[attribute]})
        # Not needed for the session assignment
        elif key_name == "ResponseMetaData":
            break

    return result

@user_factory.route("/login_admin")
def login_admin():
    print("hit route")
    key = request.args.get('key')
    try:
        print(session['user_id'])
    except:
        print('no user set')
    if key == os.getenv("FLASK_SECRET_KEY").replace("+", " "):
        session['user_id'] = 17
        session['ID'] = 1
        session['username'] = 'machine'
        session['roles'] = 'administrator'
        return jsonify({"message": "success"})
    return jsonify({"message": "failure"})


@user_factory.route("/users/register", methods=['GET'])
def register_user():
    try:
        data = {
            "grant_type": "authorization_code",
            "code": request.args.get('code'),
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": f"{FLASK_URI}/users/register",
        }
        token_res = requests.post(TOKEN_URL, data=data)
        token = json.loads(token_res.text)["access_token"]
        # user has successfully logged in, now querying oauth server for user details like name, email, etc.
        user_info_res = requests.get(USERINFO_URL + f"?access_token={token}")
        user_info = json.loads(user_info_res.text)

        session['email'] = user_info['user_email']
        session['roles'] = user_info['user_roles']
        session['username'] = user_info['user_nicename']
        session['ID'] = user_info['ID']
        session['expiration'] = time.time() + 3600
        # assume user is first time login and try to create user
        role = "administrator" if "administrator" in session['roles'] else "guest"
        user = Users(wordpress_id=user_info['ID'], username=user_info['user_nicename'], security_role=role,
                     date_created=datetime.now(), email=user_info['user_email'])
        new_user = True
        try:
            result = db.session.query(Users).filter(or_(Users.email == user_info['user_email'], Users.wordpress_id == user_info['ID'])).first()
            if result:
                user = result
                new_user = False
                print("found user")
                session['roles'] = [user.security_role]
                session['username'] = user.username
                if not user.wordpress_id:
                    user.wordpress_id = user_info['ID']
                    db.session.add(user)
                    db.session.commit()
        except Exception as ex:
            print(ex)
        try:
            user.token = token
            user.expiration = int(time.time()) + 3600
            if new_user:
                db.session.add(user)
            db.session.commit()
        except Exception as ex:
            return jsonify({"message": f"error creating user in database {ex}"})

        # either user was new and created, or exists already
        # retrieve user from DB and set cookie using data from DB
        try:
            user = db.session.query(Users).filter(Users.wordpress_id == user_info['ID']).first()
            session['user_id'] = user.database_id
        except Exception as ex:
            print("user was created, but error retrieving from database", ex)
        try:
            user.last_login = datetime.now()
            db.session.add(user)
            db.session.commit()
        except Exception as ex:
            print(f"unable to set last login for user {str(ex)}")

        # check for email and update if necessary
        try:
            assert user.email
        except:
            user.email = user_info['user_email']

        try:
            default = db.session.query(ItemCollections).filter_by(user_id=session['user_id'], name='default').first()
            if not default:
                default = ItemCollections(user_id=session['user_id'], name='default')
                db.session.add(default)
                db.session.commit()
        except Exception as ex:
            print("unable to locate or create a default collection for", session["user_id"], ex)

        response = make_response(redirect(session["return_url"]))
        user_data = {'email': user_info['user_email'], 'nicename': user_info['user_nicename'],
                     'wordpress_id':user_info['ID'], 'id': session['user_id'], 'role': session['roles']}
        session['userInfo'] = user_data
        return response
    except Exception as ex:
        return jsonify({"message":str(ex)})


@user_factory.cli.command("check")
def build_check():
    print("just a build check")


@user_factory.route("/users/logout", methods=['GET'])
def clear_session():
    try:
        del session['user_id']
        del session['roles']
        del session['ID']
    except Exception as ex:
        print(ex)
    return jsonify({"message": "success"})


def unique_id():
    return hash(time.time())


@user_factory.route("/users/login_as_guest", methods=['GET'])
def login_as_guest():
    try:
        time_hash = str(unique_id())[:8]
        guest_user = Users(username=f"guest-{time_hash}", security_role="guest", date_created=datetime.now(), credit=0)
        try:
            db.session.add(guest_user)
            db.session.commit()
            default = ItemCollections(user_id=guest_user.database_id, name='default')
            db.session.add(default)
            db.session.commit()
        except Exception as ex:
            print(ex)
            db.session.rollback()
            return jsonify({"message": "failure"})
        session['user_id'] = guest_user.database_id
        session['roles'] = ["guest"]
        session['username'] = guest_user.username
        session['ID'] = 0
    except Exception as ex:
        print(ex)
    return jsonify({"message": "success"})
