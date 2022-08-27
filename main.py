from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from dotenv import load_dotenv
import jwt

import os
import re
from datetime import datetime

from database import Database

if os.path.isfile(".env"):
    load_dotenv()

app = Flask(__name__)
app.config.from_mapping(dict(os.environ))

database = Database(os.getenv("MONGO_URI"))

def verify_session():
    if 'user' in session:
        try:
            decoded = jwt.decode(session['user'], os.getenv('TOKEN'), algorithms=["HS256"])
            if decoded['expires_at'] > int(datetime.now().timestamp()):
                return decoded
        except:
            pass
        session.pop('user', None)
    return False

@app.route("/")
def index():
    ses = verify_session()
    if ses:
        user = database.getUserWithId(ses['_id'])
        projects = database.getUserProjects(ses['_id'])
        return render_template("user.html", user=user, projects=projects)
    return render_template("index.html")

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route("/new", methods=["GET", "POST"])
def new():
    ses = verify_session()
    if ses:
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
            database.addProject(ses['_id'], name, newUrls)
            return redirect(url_for('index'))
        return render_template("new.html", error=None)
    return redirect(url_for('index'))

@app.route("/project/<id>")
def project_view(id):
    ses = verify_session()
    if ses:
        project = database.getProject(ses['_id'], id)
        if project:
            return render_template("project.html", project=project)
    return redirect(url_for('index'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if 'user' not in session:
        if request.method == "POST":
            form = dict(request.form)
            if 'email' not in form or 'username' not in form or 'password' not in form:
                return render_template("register.html", error="Missing Values"), 400
            for val in list(form.values()):
                if val.replace(" ", "") == '' or val is None:
                    return render_template("register.html", error="Empty Value"), 400
            if database.userExists(form['email']):
                return render_template("register.html", error="Email already exist"), 400
            user = database.addUser(form)
            ses = database.generateSession(user['_id'])
            session['user'] = ses
            return redirect(url_for('index'))
        return render_template("register.html", error=None)

@app.route("/login", methods=["GET", "POST"])
def login():
    if 'user' not in session:
        if request.method == "POST":
            form = dict(request.form)
            if 'email' not in form or 'password' not in form:
                return render_template("login.html", error="Missing Values"), 400
            for val in list(form.values()):
                if val.replace(" ", "") == '' or val is None:
                    return render_template("login.html", error="Empty Value"), 400
            if not database.userExists(form['email']):
                return render_template("login.html", error="User doesn't Exist"), 400
            user = database.getUser(form['email'])
            ses = database.generateSession(user['_id'])
            session['user'] = ses
            return redirect(url_for('index'))
        return render_template("login.html", error=None)

if __name__ == "__main__":
    app.run(debug=True)

