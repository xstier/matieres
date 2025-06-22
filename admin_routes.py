from flask import Blueprint, render_template, session, redirect, url_for, request, flash , jsonify
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

admin = Blueprint('admin', __name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["matieres"]

# Exemple : collection des matières
matieres_col = db["matieres"]
users_col = db["users"]
themes_col = db["themes"]

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
@admin.route('/exercice_interactif/add', methods=['GET', 'POST'])
def add_exercice_interactif():
    matieres = list(db.matieres.find())
    if request.method == 'POST':
        matiere_id = request.form.get('matiere_id')
        theme_id = request.form.get('theme_id')
        titre = request.form.get('titre')
        question = request.form.get('question')
        reponse_html = request.form.get('reponse_html')

        # Ici, tu peux ajouter la validation et insertion dans la base
        exercice = {
            'matiere_id': ObjectId(matiere_id),
            'theme_id': ObjectId(theme_id),
            'titre': titre,
            'question': question,
            'reponse_html': reponse_html,
            'created_at': datetime.now()
        }
        db.exercices_interactifs.insert_one(exercice)
        flash("Exercice interactif créé avec succès !")
        return redirect(url_for('admin.admin_home'))

    return render_template('add_exercice_interactif.html', matieres=matieres)
@admin.route('/themes')
@admin_required
def list_themes():
    themes = list(themes_col.find())
    matieres_dict = {m["_id"]: m["nom"] for m in matieres_col.find()}
    for theme in themes:
        theme["matiere_nom"] = matieres_dict.get(theme["matiere_id"], "Inconnue")
    return render_template("admin/themes_list.html", themes=themes)

@admin.route('/themes/add', methods=['GET', 'POST'])
@admin_required
def add_theme():
    matieres = list(matieres_col.find())
    if request.method == 'POST':
        nom = request.form.get("nom", "").strip()
        description = request.form.get("description", "").strip()
        matiere_id = request.form.get("matiere_id")

        if not nom or not matiere_id:
            flash("Tous les champs sont obligatoires.")
            return render_template("admin/themes_add.html", matieres=matieres)

        themes_col.insert_one({
            "nom": nom,
            "description": description,
            "matiere_id": ObjectId(matiere_id),
            "created_at": datetime.now()
        })
        flash("Thème ajouté avec succès.")
        return redirect(url_for("admin.list_themes"))

    return render_template("admin/themes_add.html", matieres=matieres)

# Modifier un thème
@admin.route('/themes/edit/<theme_id>', methods=['GET', 'POST'])
@admin_required
def edit_theme(theme_id):
    theme = themes_col.find_one({"_id": ObjectId(theme_id)})
    if not theme:
        flash("Thème introuvable.")
        return redirect(url_for("admin.list_themes"))

    matieres = list(matieres_col.find())

    if request.method == 'POST':
        nom = request.form.get("nom", "").strip()
        description = request.form.get("description", "").strip()
        matiere_id = request.form.get("matiere_id")

        if not nom or not matiere_id:
            flash("Tous les champs sont requis.")
            return render_template("admin/themes_edit.html", theme=theme, matieres=matieres)

        themes_col.update_one({"_id": ObjectId(theme_id)}, {"$set": {
            "nom": nom,
            "description": description,
            "matiere_id": ObjectId(matiere_id),
            "updated_at": datetime.now()
        }})
        flash("Thème modifié avec succès.")
        return redirect(url_for("admin.list_themes"))

    return render_template("admin/themes_edit.html", theme=theme, matieres=matieres)

# Supprimer un thème
@admin.route('/themes/delete/<theme_id>', methods=['POST'])
@admin_required
def delete_theme(theme_id):
    themes_col.delete_one({"_id": ObjectId(theme_id)})
    flash("Thème supprimé.")
    return redirect(url_for("admin.list_themes"))
from flask import jsonify

@admin.route('/api/themes/<matiere_id>')
def api_get_themes(matiere_id):
    from bson.objectid import ObjectId

    try:
        themes = list(db.themes.find({"matiere_id": ObjectId(matiere_id)}))
        # Convertir ObjectId en str pour JSON
        for theme in themes:
            theme['_id'] = str(theme['_id'])
            theme['matiere_id'] = str(theme['matiere_id'])
        return jsonify(themes)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

