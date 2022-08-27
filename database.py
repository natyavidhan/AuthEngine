from pymongo import MongoClient
import bcrypt
import jwt

from uuid import uuid4
import random
from datetime import timedelta, datetime
import requests
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class Database:
    def __init__(self, URL):
        self.client = MongoClient(URL)
        self.db = self.client.core
        self.users = self.db.users
        self.allProjects = self.db.projects
        self.projects = self.client.projects
        
    def addUser(self, user):
        id =str(uuid4())
        user = {
            '_id': id,
            'username': user['username'],
            'email': user['email'],
            'password': bcrypt.hashpw(user['password'].encode('utf-8'), bcrypt.gensalt()),
            'projects': [],
            'is_verified': False,
            'created': datetime.now().strftime("%d %B %Y, %I:%M:%S %p")
        }
        self.users.insert_one(user)
        self.send_mail(user['_id'])
        return user

    def send_mail(self, user_id):
        user = self.getUserWithId(user_id)
        message = MIMEMultipart("alternative")
        message["Subject"] = "Verify your email"
        message["From"] = os.getenv('EMAIL')
        message["To"] = user['email']

        encoded = jwt.encode({'_id': user['_id']}, os.getenv('TOKEN'), algorithm='HS256')

        url = os.getenv('DOMAIN') + '/auth/verify?token=' + encoded

        html = """
        <h1 style="text-align: center;">AuthLib Email Verification</h1>
        <br>
        <h3 style="text-align: center;">
            <font size="5">
                Hello {user},
                <br>
                Please <a href="{url}" target="_blank">Click this link</a> to Verify your account
            </font>
        </h3>
        """.format(user=user['username'], url=url)

        html = MIMEText(html, "html")
        message.attach(html)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            print(os.getenv('EMAIL'), os.getenv('EMAIL_PASS'))
            server.login(os.getenv('EMAIL'), os.getenv('EMAIL_PASS'))
            server.sendmail(os.getenv('EMAIL'), user['email'], message.as_string())
    
    def userExists(self, email):
        return self.users.find_one({'email': email}) is not None
    
    def getUser(self, email):
        return self.users.find_one({'email': email})
    
    def getUserWithId(self, id):
        return self.users.find_one({'_id': id})

    def addProject(self, userid, name, urls):
        id = "".join(random.choice("0123456789abcdef") for i in range(26))
        self.users.update_one({'_id': userid}, {'$push': {'projects': [id, name]}})
        self.allProjects.insert_one({
            '_id': id,
            'owner': userid,
            'name': name,
            'urls': urls,
            'private_id': str(uuid4()),
            'created': datetime.now().strftime("%d %B %Y, %I:%M:%S %p")
        })

    def getUserProjects(self, userid):
        return [i for i in self.allProjects.find({"owner": userid})]

    def getProject(self, userid, projectid):
        return self.allProjects.find_one({"owner": userid, "_id": projectid})

    def generateSession(self, user_id):
        return jwt.encode({'_id': user_id, 'expires_at': int((datetime.now()+timedelta(30)).timestamp())}, os.getenv('TOKEN'), algorithm='HS256')
