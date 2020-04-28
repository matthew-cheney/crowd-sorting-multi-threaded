from flask import request, abort, redirect, url_for
from functools import wraps

from crowdsorting.app_resources import DBProxy


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # print("checking login ..............................................................")
        email = request.cookies.get('email', None)
        cid = request.cookies.get('cid', None)
        if not DBProxy.verify_login(email, cid):
            return redirect(url_for('home'))
        else:
            # print("you're ok")
            return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        email = request.cookies.get('email', None)
        if not DBProxy.check_admin(email):
            abort(401)
        else:
            return fn(*args, **kwargs)
    return wrapper

def valid_current_project(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        email = request.cookies.get('email', None)
        project = request.cookies.get('current_project', None)
        if not DBProxy.verify_user_in_project(email, project_name=project):
            return redirect(url_for('dashboard'))
        else:
            # print("you're ok")
            return fn(*args, **kwargs)
    return wrapper
