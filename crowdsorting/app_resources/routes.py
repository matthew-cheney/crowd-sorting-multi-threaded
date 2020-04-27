from flask import render_template, redirect, url_for

from crowdsorting import app
from crowdsorting.app_resources import StringList


@app.route('/', methods=['GET'])
@app.route('/home', methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():

    return render_template('userdashboard.html', StringList=StringList)
