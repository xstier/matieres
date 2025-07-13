from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from pymongo import MongoClient
from constants import ROLES,CLASSES

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
            
            session["classe"] = user.get("classe","")

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
            elif role =="eleve":
                return redirect(url_for("eleve.home_eleve"))
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
    current_user_role = session.get("role")

    # Bloquer les utilisateurs connectés sans droits suffisants
    if current_user_role and current_user_role not in [ROLES["ADMIN"], ROLES["PROFESSEUR"]]:
        flash("Vous n'avez pas accès à cette page.")
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        selected_classes = request.form.getlist("classe")
        requested_role = request.form.get("role", ROLES["USER"])

        if not name or not username or not password or not selected_classes:
            flash("Tous les champs sont obligatoires.")
            return render_template(
                "register.html",
                name=name,
                username=username,
                selected_classes=selected_classes,
                classes_list=CLASSES,
                roles=ROLES
            )

        if users_col.find_one({"username": username}):
            flash("Ce nom d'utilisateur est déjà pris.")
            return render_template(
                "register.html",
                name=name,
                username=username,
                selected_classes=selected_classes,
                classes_list=CLASSES,
                roles=ROLES
            )

        # Attribution du rôle selon permissions
        if current_user_role == ROLES["ADMIN"]:
            role = requested_role
        elif current_user_role == ROLES["PROFESSEUR"]:
            role = requested_role if requested_role in [ROLES["PROFESSEUR"], ROLES["ELEVE"]] else ROLES["ELEVE"]
        else:
            # Non connecté → rôle automatique "user"
            role = ROLES["USER"]

        hashed_pw = generate_password_hash(password)
        users_col.insert_one({
            "name": name,
            "username": username,
            "password": hashed_pw,
            "role": role,
            "created_at": datetime.now(),
            "classe": selected_classes
        })

        flash("Inscription réussie.")

        # Connexion automatique si non connecté
        if not current_user_role:
            session.clear()
            session["username"] = username
            session["name"] = name
            session["role"] = role
            session["admin"] = role == ROLES["ADMIN"]
            session["classe"] = selected_classes
            return redirect(url_for("index"))

        # Redirection selon le rôle du créateur
        return redirect(
            url_for("admin.admin_home") if current_user_role == ROLES["ADMIN"] else url_for("prof.admin_prof")
        )

    return render_template(
        "register.html",
        selected_classes=[],
        classes_list=CLASSES,
        roles=ROLES
    )


