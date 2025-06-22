import os
from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from werkzeug.utils import secure_filename

admin = Blueprint('admin', __name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["matieres"]
matieres_col = db["matieres"]
users_col = db["users"]
themes_col = db["themes"]




ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Accès correct au chemin d’upload depuis la config Flask
def get_upload_path():
    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        raise RuntimeError("UPLOAD_FOLDER n'est pas défini dans app.config")
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder




# Middleware simple pour vérifier si l'utilisateur est admin
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin"):
            flash("🔒 Redirection déclenchée depuis :"+ request.path)
            flash("Accès réservé aux administrateurs.")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


@admin.route('/admin')
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

        if not nom:
            flash("Le nom de la matière est obligatoire.")
            return render_template("admin/matieres_add.html")

        matiere_exist = matieres_col.find_one({"nom": nom})
        if matiere_exist:
            flash("Cette matière existe déjà.")
            return render_template("admin/matieres_add.html")

        matieres_col.insert_one({
            "nom": nom,
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
@admin_required
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

@admin.route('/admin/lessons/add', methods=['GET', 'POST'])
@admin_required
def add_lesson():
    matieres = list(matieres_col.find())

    if request.method == 'POST':
        matiere_id = request.form.get('matiere_id')
        theme_id = request.form.get('theme_id')
        titre = request.form.get('titre', '').strip()
        contenu = request.form.get('contenu', '').strip()
        fichier = request.files.get('fichier')

        # Vérification des champs obligatoires
        if not matiere_id or not theme_id or not titre:
            flash("Tous les champs obligatoires n'ont pas été remplis.")
            return render_template('admin/lesson_add.html', matieres=matieres)

        if not contenu and (not fichier or fichier.filename == ""):
            flash("Vous devez fournir une description ou un fichier.")
            return render_template('admin/lesson_add.html', matieres=matieres)

        # Traitement du fichier si présent
        file_path = None
        if fichier and allowed_file(fichier.filename):
            filename = secure_filename(fichier.filename)
            upload_folder = current_app.config.get("UPLOAD_FOLDER")

            if not upload_folder:
                flash("UPLOAD_FOLDER non défini dans la configuration.")
                return render_template('admin/lesson_add.html', matieres=matieres)

            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)
            fichier.save(filepath)
            file_path = os.path.relpath(filepath, 'static')  # pour usage dans les templates

        # Objet leçon à ajouter dans le thème
        lesson_obj = {
            "titre": titre,
            "contenu": contenu,
            "fichier": file_path,  # relatif à /static
            "created_at": datetime.now()
        }

        # Mise à jour du thème
        themes_col.update_one(
            {"_id": ObjectId(theme_id)},
            {"$push": {"lessons": lesson_obj}}
        )

        flash("Leçon ajoutée avec succès.")
        return redirect(url_for('admin.list_themes'))

    return render_template('admin/lesson_add.html', matieres=matieres)



@admin.route('/lecon/edit/<theme_id>/<int:index>', methods=["GET", "POST"])
@admin_required
def edit_lecon(theme_id, index):
    theme = themes_col.find_one({"_id": ObjectId(theme_id)})
    if not theme:
        flash("Thème introuvable.")
        return redirect(url_for("admin.list_themes"))

    lessons = theme.get("lessons", [])
    if index < 0 or index >= len(lessons):
        flash("Leçon introuvable.")
        return redirect(url_for("admin.list_themes"))

    if request.method == "POST":
        titre = request.form.get("titre", "").strip()
        contenu = request.form.get("contenu", "").strip()
        fichier = request.files.get("fichier")

        if not titre or not contenu:
            flash("Titre et contenu sont obligatoires.")
            return render_template("admin/lesson_edit.html", theme=theme, lesson=lessons[index])

        lesson = lessons[index]
        lesson["titre"] = titre
        lesson["contenu"] = contenu

        if fichier and fichier.filename:
            if '.' in fichier.filename and fichier.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
                filename = secure_filename(fichier.filename)
                filepath = os.path.join("static/uploads", filename)
                fichier.save(filepath)
                lesson["fichier"] = filename
            else:
                flash("Extension de fichier non autorisée.")
                return render_template("admin/lesson_edit.html", theme=theme, lesson=lessons[index])

        themes_col.update_one({"_id": ObjectId(theme_id)}, {"$set": {"lessons": lessons}})
        flash("Leçon mise à jour avec succès.")
        return redirect(url_for("afficher_lecon", theme_id=theme_id, lesson_index=index))

    return render_template("admin/lesson_edit.html", theme=theme, lesson=lessons[index])


@admin.route('/lecon/delete/<theme_id>/<int:index>', methods=["POST"])
@admin_required
def delete_lecon(theme_id, index):
    theme = themes_col.find_one({"_id": ObjectId(theme_id)})
    if not theme:
        flash("Thème introuvable.")
        return redirect(url_for("admin.list_themes"))

    lessons = theme.get("lessons", [])
    if index < 0 or index >= len(lessons):
        flash("Leçon introuvable.")
        return redirect(url_for("admin.list_themes"))

    del lessons[index]
    themes_col.update_one({"_id": ObjectId(theme_id)}, {"$set": {"lessons": lessons}})

    flash("Leçon supprimée avec succès.")
    return redirect(url_for("afficher_themes", matiere_id=theme["matiere_id"]))

