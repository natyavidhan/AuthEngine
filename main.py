from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from authlib.integrations.flask_client import OAuth
from loginpass import create_flask_blueprint, GitHub
from dotenv import load_dotenv

import os

from database import Database

if os.path.isfile(".env"):
    load_dotenv()

app = Flask(__name__)
app.config.from_mapping(dict(os.environ))

oauth = OAuth(app)

database = Database(os.getenv("MONGO_URI"))
backends = [GitHub]

@app.route("/")
def index():
    if 'user' not in session:
        return render_template("index.html")
    return render_template("user.html", user=session['user'])

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

def handle_authorize(remote, token, user_info):
    if not database.userExists(user_info['email']):
        database.addUser(user_info)
    session['user'] = database.getUser(user_info['email'])
    return redirect(url_for('index'))

bp = create_flask_blueprint(backends, oauth, handle_authorize)
app.register_blueprint(bp, url_prefix='/')

if __name__ == "__main__":
    app.run(debug=True)