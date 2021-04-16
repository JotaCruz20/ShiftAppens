from flask import Flask, render_template, request, redirect

app = Flask(__name__)
app.debug = True
counter = 2


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/loggedIn', methods=['GET', 'POST'])
def loggedIn():
    if request.method == 'POST':
        mins = request.form['mins']
        hour = request.form['hour']
        
        # funcao aqui
        return render_template('logIn.html')
    else:
        return render_template('logIn.html')


@app.route("/callback/q")
def callback():
    return


if __name__ == '__main__':
    app.run(debug=True)
