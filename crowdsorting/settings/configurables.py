import os

from crowdsorting import app

CAS_EMAIL_EXTENSION = '@byu.edu'
COOKIE_KEY = 'ef47d20f9cd74832b6713b8597db06df'
ADMIN_PATH = os.path.join(app.config['APP_ROOT'], 'settings/admins.txt')