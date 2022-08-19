from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from authlib.integrations.flask_client import OAuth
from loginpass import create_flask_blueprint, GitHub
from dotenv import load_dotenv

import os
import re

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
    projects = database.getUserProjects(session['user']['_id'])
    return render_template("user.html", user=session['user'], projects=projects)

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route("/new", methods=["GET", "POST"])
def new():
    if 'user' in session:
        if request.method == "POST":
            name = request.form['name']
            urls = request.form['redirect'].split(" ")
            newUrls = []
            for url in urls:
                if re.match(r"^(http|https)://[a-zA-Z0-9-.]+\.[a-zA-Z]{2,3}(/\S*)?$", url):
                    newUrls.append(url)
                elif re.match(r"^(http|https)://([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|localhost):[0-9]{1,5}(/\S*)?$", url):
                    newUrls.append(url)
                else:
                    return render_template("new.html", error="Invalid URL")
            database.addProject(session['user']['_id'], name, newUrls)
            return redirect(url_for('index'))
        return render_template("new.html", error=None)
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

