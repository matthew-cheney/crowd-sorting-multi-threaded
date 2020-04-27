from math import floor

import requests
from flask_login import login_user, logout_user

from crowdsorting.app_resources.DBHandler import DBHandler
from crowdsorting import app, cas, session, pairselectors, \
    pairselector_options, GOOGLE_DISCOVERY_URL, client, login_manager, \
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from flask import abort
from flask import flash, send_file
from flask import render_template
from flask import url_for
from flask import redirect
from flask import request
from flask import make_response
import os

from . import Strings_List as StringList
from .RejectLogger import RejectLogger
from .settings import ADMIN_PATH, PM_PATH, DEFAULT_LANDING_PAGE
from .user import User
import json
import re
import time

from functools import wraps

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # print("checking login ..............................................................")
        try:
            if not dbhandler.check_cid(session['user'].get('email'), session['user'].get('cid')):
                return "This page is solely accessible to users", 403
            else:
                # print("you're ok")
                return fn(*args, **kwargs)
        except KeyError:
            print(session)
            return "This page is only accessible to users", 403
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not isAdmin():
            return "This page is only accessible to administrators", 403
        else:
            return fn(*args, **kwargs)
    return wrapper