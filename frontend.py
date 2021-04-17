from flask import Flask, render_template, request, redirect, jsonify
import requests
import json
import time
from flask_simple_geoip import SimpleGeoIP
import pandas as pd
import pycountry
import re

dictOfCountrys = {}


app = Flask(__name__)
app.debug = True
app.config.update(GEOIPIFY_API_KEY='at_JobnKp9xFWI5TJ2VfJWptHaQpKQDH')
simple_geoip = SimpleGeoIP(app)



@app.route('/')
def hello_world():
    return render_template('index.html')


def getAtributeQuadrante(x, y):
    if (x >= 2.5 and y >= 0 and y <= 2.5) or (x >= 2.5 and y >= 2.5):
        return 'Happy'
    elif 0 <= x <= 2.5 and y >= 2.5:
        return 'Exuberant'
    elif 0 <= x <= 2.5 and 0 <= y <= 2.5:
        return 'Energetic'
    elif (0 <= x <= 2.5 and 0 >= y >= -2.5) or (0 <= x <= 2.5 and y <= -2.5) or (x >= 2.5 and 0 >= y >= -2.5):
        return 'Calm'
    elif x >= 2.5 and y <= -2.5:
        return 'Content'
    elif (0 >= x >= -2.5 and 0 <= y <= 2.5) or (0 >= x >= -2.5 and y >= 2.5):
        return "Anxious"
    elif (0 >= x >= -2.5 >= y) or (x <= -2.5 and y <= -2.5):
        return 'Depression'
    elif x <= -2.5 and y >= 2.5:
        return 'Frantic'
    elif (x <= -2.5 and 0 <= y <= 2.5) or (0 >= x >= -2.5 and 0 >= y >= -2.5) or (x <= -2.5 <= y <= 0):
        return 'Sad'


@app.route('/loggedIn', methods=['GET', 'POST'])
def loggedIn():
    if request.method == 'POST':
        # mins = request.form['mins']
        # hour = request.form['hour']
        # miliseconds = hour * 60 * 60 * 1000 + mins * 60 * 1000
        # print(request.form)

        x = int(request.form['emotion'])
        y = int(request.form['energy'])

        suicidal = int(request.form['life'])

        if suicidal <= 2:
            geoip_data = simple_geoip.get_geoip_data()
            country = geoip_data['location']['country']

            country = 'PT'  # isto e so debug
            infoCountry = pycountry.countries.get(alpha_2=country)
            infoCalls = dictOfCountrys[infoCountry.name]

            infoCalls = infoCalls.replace('(', '<').replace(')', '>')
            infoCalls = re.sub('<[^>]+>', '', infoCalls)
            infoSplit = infoCalls.split('.')
            str = ''
            for info in infoSplit:
                str += info+'\n'
            str = str.replace('  ', ' ').replace(' \n', '')
            mood = 'Depressed'

            # funcao aqui
            return render_template('getHelp.html', info=str)

        mood = getAtributeQuadrante(x, y)

        # funcao aqui
        return render_template('logIn.html')
    else:
        return render_template('logIn.html')


@app.route("/callback/q")
def callback():
    return


def getCountriesList():
    global dictOfCountrys
    dfs = pd.read_html('https://en.wikipedia.org/wiki/List_of_suicide_crisis_lines')
    lista = dfs[0].values.tolist()
    dictOfCountrys = dict(lista)


if __name__ == '__main__':
    getCountriesList()
    app.run(debug=True)
