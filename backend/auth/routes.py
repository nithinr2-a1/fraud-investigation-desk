from flask import render_template, request, redirect, url_for, flash
from flask_login import (
    login_user,
    logout_user,
    login_required,
    UserMixin
)
from werkzeug.security import check_password_hash
from bson import ObjectId

from . import auth_bp
from extensions import login_manager
from db import users


# ---------------------------------------
# User Class
# ---------------------------------------
class User(UserMixin):
    def __init__(self, user):
        self.id = str(user["_id"])
        self.username = user["username"]
        self.role = user.get("role", "User")
        self.name = user.get("name", "")
        self.email = user.get("email", "")


# ---------------------------------------
# Flask Login Loader
# ---------------------------------------
@login_manager.user_loader
def load_user(user_id):
    try:
        user = users.find_one({"_id": ObjectId(user_id)})

        if user:
            return User(user)

    except Exception:
        pass

    return None


# ---------------------------------------
# Login
# ---------------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        user = users.find_one({"username": username})

        if user:

            if check_password_hash(user["password"], password):

                login_user(User(user))

                flash("Login Successful", "success")

                return redirect(url_for("dashboard"))

        flash("Invalid Username or Password", "danger")

    return render_template("login.html")


# ---------------------------------------
# Logout
# ---------------------------------------
@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully.", "info")

    return redirect(url_for("auth.login"))