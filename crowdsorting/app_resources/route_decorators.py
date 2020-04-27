from flask import request, abort
from functools import wraps

from crowdsorting.app_resources import DBProxy


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # print("checking login ..............................................................")
        email = request.cookies.get('email', None)
        cid = request.cookies.get('cid', None)
        if not DBProxy.verify_login(email, cid):
            print('aborting')
            abort(401)
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