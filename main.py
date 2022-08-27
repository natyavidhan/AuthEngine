from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from dotenv import load_dotenv

import os
import re

from database import Database

if os.path.isfile(".env"):
    load_dotenv()

app = Flask(__name__)
app.config.from_mapping(dict(os.environ))

database = Database(os.getenv("MONGO_URI"))

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

@app.route("/project/<id>")
def project_view(id):
    if 'user' in session:
        project = database.getProject(session['user']['_id'], id)
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
            session['user'] = user
            return redirect(url_for('index'))
        return render_template("register.html", error=None)

if __name__ == "__main__":
    app.run(debug=True)

