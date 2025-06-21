from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from pymongo import MongoClient
from datetime import datetime

admin = Blueprint('admin', __name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["matieres"]

# Exemple : collection des matières
matieres_col = db["matieres"]
users_col = db["users"]

# Middleware simple pour vérifier si l'utilisateur est admin
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin"):
            flash("Accès réservé aux administrateurs.")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


@admin.route('/')
@admin_required
def admin_home():
    return render_template("admin/home.html")

# Liste des matières
@admin.route('/matieres')
@admin_required
def list_matieres():
    matieres = list(matieres_col.find())
    return render_template("admin/matieres_list.html", matieres=matieres)

# Ajouter une matière
@admin.route('/matieres/add', methods=['GET', 'POST'])
@admin_required
def add_matiere():
    if request.method == 'POST':
        nom = request.form.get("nom", "").strip()
        description = request.form.get("description", "").strip()

        if not nom:
            flash("Le nom de la matière est obligatoire.")
            return render_template("admin/matieres_add.html")

        matiere_exist = matieres_col.find_one({"nom": nom})
        if matiere_exist:
            flash("Cette matière existe déjà.")
            return render_template("admin/matieres_add.html")

        matieres_col.insert_one({
            "nom": nom,
            "description": description,
            "created_at": datetime.now()
        })
        flash("Matière ajoutée avec succès.")
        return redirect(url_for("admin.list_matieres"))

    return render_template("admin/matieres_add.html")

# Modifier une matière
@admin.route('/matieres/edit/<matiere_id>', methods=['GET', 'POST'])
@admin_required
def edit_matiere(matiere_id):
    from bson.objectid import ObjectId

    matiere = matieres_col.find_one({"_id": ObjectId(matiere_id)})
    if not matiere:
        flash("Matière introuvable.")
        return redirect(url_for("admin.list_matieres"))

    if request.method == 'POST':
        nom = request.form.get("nom", "").strip()
        description = request.form.get("description", "").strip()

        if not nom:
            flash("Le nom de la matière est obligatoire.")
            return render_template("admin/matieres_edit.html", matiere=matiere)

        # Vérifier s’il n’y a pas un doublon (sauf la matière courante)
        duplicate = matieres_col.find_one({"nom": nom, "_id": {"$ne": ObjectId(matiere_id)}})
        if duplicate:
            flash("Une autre matière avec ce nom existe déjà.")
            return render_template("admin/matieres_edit.html", matiere=matiere)

        matieres_col.update_one({"_id": ObjectId(matiere_id)}, {"$set": {
            "nom": nom,
            "description": description,
            "updated_at": datetime.now()
        }})
        flash("Matière mise à jour avec succès.")
        return redirect(url_for("admin.list_matieres"))

    return render_template("admin/matieres_edit.html", matiere=matiere)

# Supprimer une matière
@admin.route('/matieres/delete/<matiere_id>', methods=['POST'])
@admin_required
def delete_matiere(matiere_id):
    from bson.objectid import ObjectId
    matieres_col.delete_one({"_id": ObjectId(matiere_id)})
    flash("Matière supprimée.")
    return redirect(url_for("admin.list_matieres"))
