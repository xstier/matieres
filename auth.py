from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from pymongo import MongoClient

auth = Blueprint('auth', __name__)
client = MongoClient("mongodb://localhost:27017/")
db = client["matieres"]
users_col = db["users"]

@auth.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = users_col.find_one({"username": username})
        if user and check_password_hash(user["password"], password):
            session.clear()
            session["username"] = user["username"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            if user["role"] == "admin":
                session["admin"] = True
                return redirect(url_for("admin.admin_home"))
            else:
                return redirect(url_for("index"))
        message = "Identifiants incorrects."
    return render_template("login.html", message=message)

@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@auth.route("/register", methods=["GET", "POST"])
def register():
    message = ""
    name = ""
    username = ""

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user")

        if users_col.find_one({"username": username}):
            message = "Nom d'utilisateur déjà utilisé."
        else:
            hashed_pw = generate_password_hash(password)
            if not session.get("admin"):
                role = "user"

            users_col.insert_one({
                "name": name,
                "username": username,
                "password": hashed_pw,
                "role": role,
                "created_at": datetime.now()
            })

            # Connexion auto après inscription
            session.clear()
            session["username"] = username
            session["role"] = role
            session["name"] = name
            if role == "admin":
                session["admin"] = True
                return redirect(url_for("admin.admin_home"))
            else:
                return redirect(url_for("index"))

    return render_template("register.html", message=message, name=name, username=username)


