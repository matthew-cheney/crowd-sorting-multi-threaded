from math import floor

import requests
from flask_login import login_user, logout_user

from crowdsorting.app_resources import DBProxy
from crowdsorting import app, cas, \
    GOOGLE_DISCOVERY_URL, client, \
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, cookie_crypter
from flask import abort
from flask import flash, send_file
from flask import render_template
from flask import url_for
from flask import redirect
from flask import request
from flask import make_response
import os

# from . import Strings_List as StringList
# from .RejectLogger import RejectLogger
# from .settings import ADMIN_PATH, PM_PATH, DEFAULT_LANDING_PAGE
# from .user import User
import json
import re
import time

from functools import wraps

from crowdsorting.database.models import Judge
from crowdsorting.settings.configurables import CAS_EMAIL_EXTENSION, ADMIN_PATH

SUB_ROOT = app.config['SUBDIRECTORY_ROOT']

# from crowdsorting.app_resources.forms import NewUserForm, NewProjectForm
from flask_cas import login as cas_login

import datetime

"""
3 pipelines here:

| - - - - - - - A - - - - - - - | - - - - B - - - | - - Ca - - - - Cb - - - - - - - | - - - - - D - - - - - | 
1. login (google) -> callback -> load_user ->     (newuser    | returningUser) ->    postLoadUser -> dashboard
2. cas_login ->                  load_user ->     (newuser | returningUser) ->       postLoadUser -> dashboard
3. testing_login ->              load_user ->     (newuser    | returningUser) ->    postLoadUser -> dashboard

A. Refer to google, cas, or bypass with testing_login to authenticate user.
Passes user email (for CAS, attach CAS_EMAIL_EXTENSION) to B

B. Receives email from A. Checks database. If user exists, sends to returningUser (with email).
If user does not exist, sends to new(cas)user with email.

Ca. Prompts for user info. Creates user in database (createnewuser). Sends to postLoadUser with email and cid.
Cb. Retireves cid from database. Sends to postLoadUser with email and cid.

D. Sets user admin. Sets email and cid cookies in user browser, returns the dashboard.

Also, User == Judge
"""


@app.route('/testinglogin/<email>/<password>', methods=["GET"])
def testing_login(email, password=''):
    if not password == 'Ry9HReDwAVNabDZ50ixucWwaQxuOZMqcYvrWvDHxARWShZ62N0asuOAnok7lGj6I':
        return 'Nice try! Go use the normal login.'
    return load_user(email)


@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens (yay) let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        # unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        # picture = userinfo_response.json()["picture"]
        # users_name = userinfo_response.json()["given_name"]  # or family_name

    else:
        return "User email not available or not verified by Google.", 400

    # Begin user session by logging the user in
    return load_user(users_email)


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@app.route("/cas_login")
def cas_login(other_dest=""):
    print('In the login route!')
    print(cas.username)
    return load_user(cas.username + CAS_EMAIL_EXTENSION)


# @login_manager.user_loader
def load_user(email):
    print(f'In load_user with {email}')
    # username = user.username
    if DBProxy.is_user_exists(email):
        # User already in database
        return returninguser(email)
    # New user
    return newuser(email)


"""def load_cas_user(email):
    print(f'In load_cas_user with {email}')
    # username = user.username
    print("cas_user:", username)
    user_id = DBProxy.get_cas_user(username)
    print("userID", user_id)
    if type(user_id) == type(""):
        print("new user detected")
        session['user'] = dict()
        session['user']['email'] = ""
        session['user']['cid'] = ""
        return redirect(url_for('newcasuser'))  # newcasuser()  # Login with CAS - work on this next
    else:
        email = DBProxy.get_cas_email(username)
        return returninguser(email, user_id)
"""


@app.route('/newuser', methods=['GET', 'POST'])
def newuser(email):
    dummy_user = Judge(id='null', firstName='', lastName='', email=email,
                       cid='', is_admin=False)
    return render_template('newuser.html', current_user=dummy_user,
                           title='New User')


@app.route('/createnewuser', methods=['POST'])
def createnewuser():
    email = request.form.get('email', None)
    if email is None:
        return redirect(url_for('home'))
    # Validate first/last names
    first_name = request.form.get('firstName')
    if ' ' in first_name:
        flash('names may not contain any spaces', 'danger')
        return newuser(email)
    last_name = request.form.get('lastName')
    if ' ' in last_name:
        flash('names may not contain any spaces', 'danger')
        return newuser(email)
    cid = DBProxy.create_user(request.form.get('firstName'),
                              request.form.get('lastName'),
                              email)
    return postLoadUser(email, cid)


"""@app.route('/newcasuser', methods=['GET', 'POST'])
def newcasuser():
    if 'user' in session and DBProxy.check_cid(session['user'].get('email'), session['user'].get('cid')):
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        if 'user' not in session:
            return redirect(url_for('home'))
        # Validate first/last names
        first_name = request.form.get('firstName')
        if ' ' in first_name:
            flash(StringList.space_in_first_name_error, 'danger')
            return redirect(url_for('newcasuser'))
        last_name = request.form.get('lastName')
        if ' ' in last_name:
            flash(StringList.space_in_last_name_error, 'danger')
            return redirect(url_for('newcasuser'))
        user_email = cas.username + '@byu.edu'
        print("creating cas user for", cas.username)
        cid = DBProxy.create_cas_user(request.form.get('firstName'), request.form.get('lastName'),
                              cas.username + '@byu.edu', cas.username)
        if cid == False:
            flash('Email already taken', 'danger')
            return render_template('newcasuser.html', current_user=dummyUser, title='New User')
        session['user'] = {'email': user_email, 'cid': cid}
        isInAdminFile(user_email)
        return postLoadUser()
    return render_template('newcasuser.html', current_user=dummyUser, title='New User', is_admin=DBProxy.check_admin(session['user'].get('email'), session['user'].get('cid')), is_authenticated=DBProxy.check_cid(session['user'].get('email'), session['user'].get('cid')))
"""


def returninguser(email):
    # admins = []
    # db_user_id = DBProxy.get_user(email)
    # email = DBProxy.get_email(db_user_id)
    # isInAdminFile(email)
    # isInPMFile(email)
    cid = DBProxy.get_user_cid(email)
    return postLoadUser(email, cid)


def postLoadUser(email, cid):
    # Set user admin if needed
    if is_in_admin_file(email):
        DBProxy.set_user_as_admin(email)

    cookies = {
        'email': email,
        'cid': cid
    }
    encrypted_cookies = cookie_crypter.encrypt(cookies)
    res = make_response(redirect(url_for('dashboard')))
    res.set_cookie('email', encrypted_cookies['email'])
    res.set_cookie('cid', encrypted_cookies['cid'])
    return res


@app.route("/logout_master")
def logout_master():
    print("in logout()")

    encrypted_email = request.cookies.get('email', '')

    try:
        email = cookie_crypter.decrypt({'email': encrypted_email})['email']
    except ValueError:
        email = ''


    cas = False
    if email.endswith("@byu.edu"):  # CAS user
        cas = True
    res = make_response(render_template('logout.html', cas=cas))
    res.set_cookie('email', '', max_age=0)
    res.set_cookie('cid', '', max_age=0)
    return res

@app.route('/cas_logout', methods=['GET'])
def cas_logout():
    return redirect(url_for('cas.logout'))


""""@app.route('/old_logout')
def _logout_old():
    print("in old logout")
    session.clear()
    return redirect(url_for('cas.logout'))
"""

def is_in_admin_file(email):
    with open(ADMIN_PATH, mode='r') as f:
        admins = f.read().split('\n')
    adminBool = False
    for admin in admins:
        if admin == email:
            adminBool = True
            break
    if adminBool:
        userID = DBProxy.get_user_id(email)
        for project in DBProxy.get_all_projects():
            DBProxy.add_user_to_project(userID,
                                        project.name)
    return adminBool


"""def isInPMFile(email):
    with open(PM_PATH, mode='r') as f:
        pms = f.read().split('\n')
    pmBool = False
    for pm in pms:
        if pm == email:
            pmBool = True
            break
    return pmBool
"""
