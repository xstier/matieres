from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from pymongo import MongoClient

auth = Blueprint('auth', __name__)

# Connexion à MongoDB


client = MongoClient("mongodb://localhost:27017/")
db = client["matieres"]
users_col = db["users"]

# === ROUTE DE CONNEXION ===
@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Veuillez remplir tous les champs.")
            return render_template("login.html")

        user = users_col.find_one({"username": username})
        if user and check_password_hash(user["password"], password):
            session.clear()
            
            session["user_id"] = str(user["_id"])

            session["username"] = user["username"]
            session["name"] = user.get("name", "")
            role = user.get("role", "user").lower()

            session["role"] = role
            session["admin"] = role == "admin"

            print("Utilisateur:", user)
            print("Rôle détecté:", role)
            print("Admin ?:", session["admin"])

            if role == "admin":
                return redirect(url_for("admin.admin_home"))
            elif role == "professeur":
                return redirect(url_for("prof.admin_prof"))
            else:
                return redirect(url_for("index"))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect.")
            return render_template("login.html")

    return render_template("login.html")



# === ROUTE DE DÉCONNEXION ===
@auth.route("/logout")
def logout():
    session.clear()
    flash("Vous avez été déconnecté.")
    return redirect(url_for("index"))


# === ROUTE D'INSCRIPTION ===
@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user")

        if not name or not username or not password:
            flash("Tous les champs sont obligatoires.")
            return render_template("register.html", name=name, username=username)

        # Vérification si l'utilisateur existe
        if users_col.find_one({"username": username}):
            flash("Ce nom d'utilisateur est déjà pris.")
            return render_template("register.html", name=name, username=username)

        # Seul un admin déjà connecté peut créer un admin
        if not session.get("admin"):
            role = "user"

        hashed_pw = generate_password_hash(password)
        users_col.insert_one({
            "name": name,
            "username": username,
            "password": hashed_pw,
            "role": role,
            "created_at": datetime.now()
        })

        # Connexion automatique
        session.clear()
        session["username"] = username
        session["name"] = name
        session["role"] = role
        session["admin"] = role == "admin"

        flash("Inscription réussie.")
        if session["admin"]:
            return redirect(url_for("admin.admin_home"))
        return redirect(url_for("index"))

    return render_template("register.html")
