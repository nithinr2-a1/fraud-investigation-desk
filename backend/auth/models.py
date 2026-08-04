from flask_login import UserMixin
from db import users
from bson import ObjectId


class User(UserMixin):

    def __init__(self, user):
        self.id = str(user["_id"])
        self.username = user["username"]
        self.role = user["role"]
        self.name = user.get("name", "")

    @staticmethod
    def get(user_id):

        try:
            user = users.find_one({"_id": ObjectId(user_id)})

            if user:
                return User(user)

        except Exception:
            pass

        return None

    @staticmethod
    def get_by_username(username):

        user = users.find_one({"username": username})

        if user:
            return User(user)

        return None