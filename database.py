from pymongo import MongoClient
from uuid import uuid4
import random
import datetime
import requests

class Database:
    def __init__(self, URL):
        self.client = MongoClient(URL)
        self.db = self.client.core
        self.users = self.db.users

        self.projects = self.client.projects

        
    def addUser(self, user):
        id =str(uuid4())
        self.users.insert_one({
            '_id': id,
            'username': user['name'],
            'email': user['email'],
            'projects': [],
            'created': datetime.datetime.now().strftime("%d %B %Y, %I:%M:%S %p")
        })
    
    def userExists(self, email):
        return self.users.find_one({'email': email}) is not None
    
    def getUser(self, email):
        return self.users.find_one({'email': email})
    
    def getUserWithId(self, id):
        return self.users.find_one({'_id': id})