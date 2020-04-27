import os

from flask import Flask
from flask_cas import CAS
from flask_sqlalchemy import SQLAlchemy

from crowdsorting.app_resources.cookie_encoder import CookieCrypter
from crowdsorting.app_resources.sorting_algorithms.ACJProxy import ACJProxy
from crowdsorting.app_resources.yamlReader import yamlReader
from oauthlib.oauth2 import WebApplicationClient

app = Flask(__name__)

yamlReader.readConfig('settings/config.yaml', app)
app.config['APP_ROOT'] = os.path.dirname(os.path.abspath(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/crowdsorting.db'
app.config['SQLALCHEMY_BINDS'] = {
    'admin_data': 'sqlite:///database/admin_data.db',
    'docs': 'sqlite:///database/docs.db',
    'doc_pairs': 'sqlite:///database/doc_pairs.db'
                                  }

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

cas = CAS(app, '/cas')


GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

client = WebApplicationClient(GOOGLE_CLIENT_ID)

db = SQLAlchemy(app)

cookie_crypter = CookieCrypter()

pairselector_options = list()
pairselector_options.append(ACJProxy)

from crowdsorting.app_resources.login_routes import *
from crowdsorting.app_resources.routes import *
