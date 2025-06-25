import os
from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app, jsonify
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from werkzeug.utils import secure_filename
from functools import wraps
import bleach
from bs4 import BeautifulSoup

# Configuration du Blueprint
admin = Blueprint('admin', __name__)

# Connexion MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["matieres"]
matieres_col = db["matieres"]
users_col = db["users"]
themes_col = db["themes"]
exercices_col = db["exercices_interactifs"]

# Configuration upload
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_upload_path():
    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        raise RuntimeError("UPLOAD_FOLDER n'est pas défini dans app.config")
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder

# Middleware admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin"):
            flash("🔒 Redirection déclenchée depuis :" + request.path)
            flash("Accès réservé aux administrateurs.")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

# Routes Admin
@admin.route("/admin")
@admin_required
def admin_home():
    matieres = list(matieres_col.find())
    themes = list(themes_col.find())
    exercices = list(exercices_col.find())
    return render_template("admin/home.html", matieres=matieres, themes=themes, exercices=exercices)


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

        if matieres_col.find_one({"nom": nom}):
            flash("Cette matière existe déjà.")
            return render_template("admin/matieres_add.html")

        matieres_col.insert_one({"nom": nom, "created_at": datetime.now()})
        flash("Matière ajoutée avec succès.")
        return redirect(url_for("admin.list_matieres"))

    return render_template("admin/matieres_add.html")
@admin.route('/admin/api/themes/<matiere_id>')
@admin_required
def api_get_themes_by_matiere(matiere_id):
    try:
        themes = list(themes_col.find({'matiere_id': ObjectId(matiere_id)}))
        return jsonify([{'_id': str(t['_id']), 'nom': t['nom']} for t in themes])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# Modifier une matière
@admin.route('/matieres/edit/<matiere_id>', methods=['GET', 'POST'])
@admin_required
def edit_matiere(matiere_id):
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

        if matieres_col.find_one({"nom": nom, "_id": {"$ne": ObjectId(matiere_id)}}):
            flash("Une autre matière avec ce nom existe déjà.")
            return render_template("admin/matieres_edit.html", matiere=matiere)

        matieres_col.update_one(
            {"_id": ObjectId(matiere_id)},
            {"$set": {
                "nom": nom,
                "description": description,
                "updated_at": datetime.now()
            }}
        )
        flash("Matière mise à jour avec succès.")
        return redirect(url_for("admin.list_matieres"))

    return render_template("admin/matieres_edit.html", matiere=matiere)

# Supprimer une matière
@admin.route('/matieres/delete/<matiere_id>', methods=['POST'])
@admin_required
def delete_matiere(matiere_id):
    matieres_col.delete_one({"_id": ObjectId(matiere_id)})
    flash("Matière supprimée.")
    return redirect(url_for("admin.list_matieres"))

# Ajouter un exercice interactif
@admin.route('/exercices')
@admin_required
def list_exercices():
    exercices = list(exercices_col.find())
    themes_map = {str(t['_id']): t for t in themes_col.find()}
    matieres_map = {str(m['_id']): m['nom'] for m in matieres_col.find()}

    for ex in exercices:
        theme = themes_map.get(str(ex.get('theme_id')))
        if theme:
            ex['theme_nom'] = theme.get('nom', '❓Thème inconnu')
            ex['matiere_nom'] = matieres_map.get(str(theme.get('matiere_id')), '❓Matière inconnue')
        else:
            ex['theme_nom'] = '❓Thème inconnu'
            ex['matiere_nom'] = '❓Matière inconnue'

    return render_template('admin/exercices_list.html', exercices=exercices)

@admin.route('/exercice_interactif/add', methods=['GET', 'POST'])
@admin_required
def add_exercice_interactif():
    matieres = list(matieres_col.find())
    
    if request.method == 'POST':
        matiere_id = request.form.get('matiere_id')
        theme_id = request.form.get('theme_id')
        titre = request.form.get('titre')
        question = request.form.get('question')
        reponse_html = request.form.get('reponse_html')
        
        # Nettoyage HTML avec bleach
        allowed_tags = [
            'b', 'i', 'em', 'strong', 'u', 'br', 'p', 'div', 'span',
            'input', 'select', 'option', 'textarea', 'label', 'ul', 'ol', 'li'
        ]

        allowed_attributes = {
            '*': ['class', 'style'],
            'input': ['type', 'class', 'style', 'placeholder', 'value', 'name'],
            'select': ['class', 'style', 'name'],
            'option': ['value', 'selected'],
            'textarea': ['class', 'style', 'name', 'rows', 'cols', 'placeholder'],
            'div': ['class', 'style'],
            'span': ['class', 'style'],
            'p': ['class', 'style'],
            'label': ['for', 'class', 'style']
        }

        clean_html = bleach.clean(reponse_html, tags=allowed_tags, attributes=allowed_attributes, strip=True)

        # Extraction des réponses attendues avec BeautifulSoup
        soup = BeautifulSoup(clean_html, 'html.parser')
        bonnes_reponses = {}

        # Champs input
        for input_tag in soup.find_all('input'):
            name = input_tag.get('name')
            value = input_tag.get('value', '')
            if name:
                bonnes_reponses[name] = value

        # Champs select
        for select_tag in soup.find_all('select'):
            name = select_tag.get('name')
            selected_option = select_tag.find('option', selected=True)
            if name and selected_option:
                bonnes_reponses[name] = selected_option.get('value', '')

        # Champs textarea
        for textarea in soup.find_all('textarea'):
            name = textarea.get('name')
            if name:
                bonnes_reponses[name] = textarea.text.strip()

        # Création de l'exercice
        exercice = {
            'matiere_id': ObjectId(matiere_id),
            'theme_id': ObjectId(theme_id),
            'titre': titre,
            'question': question,
            'reponse_html': clean_html,
            'reponses_attendues': bonnes_reponses,
            'created_at': datetime.now()
        }

        exercices_col.insert_one(exercice)
        flash("Exercice interactif créé avec succès !")
        return redirect(url_for('admin.admin_home'))

    return render_template('admin/exercice_interactif_add.html', matieres=matieres)

@admin.route('/exercice_interactif/delete/<exercice_id>', methods=['POST'])
@admin_required
def delete_exercice_interactif(exercice_id):
    exercice = exercices_col.find_one({"_id": ObjectId(exercice_id)})
    if not exercice:
        flash("Exercice introuvable.", "danger")
        return redirect(url_for('admin.admin_home'))

    exercices_col.delete_one({"_id": ObjectId(exercice_id)})
    flash("Exercice supprimé avec succès.", "success")
    return redirect(url_for('admin.admin_home'))

@admin.route('/exercice_interactif/edit/<exercice_id>', methods=['GET', 'POST'])
@admin_required
def edit_exercice_interactif(exercice_id):
    exercice = exercices_col.find_one({"_id": ObjectId(exercice_id)})
    if not exercice:
        flash("Exercice introuvable.", "danger")
        return redirect(url_for('admin.admin_home'))

    matieres = list(matieres_col.find())
    themes = list(themes_col.find({"matiere_id": exercice["matiere_id"]}))

    if request.method == 'POST':
        matiere_id = request.form.get('matiere_id')
        theme_id = request.form.get('theme_id')
        titre = request.form.get('titre')
        question = request.form.get('question')
        reponse_html = request.form.get('reponse_html')

        # Nettoyage & extraction comme pour l'ajout
        allowed_tags = [
            'b', 'i', 'em', 'strong', 'u', 'br', 'p', 'div', 'span',
            'input', 'select', 'option', 'textarea', 'label', 'ul', 'ol', 'li'
        ]

        allowed_attributes = {
            '*': ['class', 'style'],
            'input': ['type', 'class', 'style', 'placeholder', 'value', 'name'],
            'select': ['class', 'style', 'name'],
            'option': ['value', 'selected'],
            'textarea': ['class', 'style', 'name', 'rows', 'cols', 'placeholder'],
            'div': ['class', 'style'],
            'span': ['class', 'style'],
            'p': ['class', 'style'],
            'label': ['for', 'class', 'style']
        }

        clean_html = bleach.clean(reponse_html, tags=allowed_tags, attributes=allowed_attributes, strip=True)

        soup = BeautifulSoup(clean_html, 'html.parser')
        bonnes_reponses = {}

        for input_tag in soup.find_all('input'):
            name = input_tag.get('name')
            value = input_tag.get('value', '')
            if name:
                bonnes_reponses[name] = value

        for select_tag in soup.find_all('select'):
            name = select_tag.get('name')
            selected_option = select_tag.find('option', selected=True)
            if name and selected_option:
                bonnes_reponses[name] = selected_option.get('value', '')

        for textarea in soup.find_all('textarea'):
            name = textarea.get('name')
            if name:
                bonnes_reponses[name] = textarea.text.strip()

        exercices_col.update_one(
            {"_id": ObjectId(exercice_id)},
            {"$set": {
                "matiere_id": ObjectId(matiere_id),
                "theme_id": ObjectId(theme_id),
                "titre": titre,
                "question": question,
                "reponse_html": clean_html,
                "reponses_attendues": bonnes_reponses,
                "updated_at": datetime.now()
            }}
        )

        flash("Exercice modifié avec succès.", "success")
        return redirect(url_for('admin.admin_home'))

    return render_template(
        'admin/exercice_interactif_edit.html',
        exercice=exercice,
        matieres=matieres,
        themes=themes
    )

# Liste des thèmes
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
        nom = request.form.get('nom', '').strip()
        matiere_id = request.form.get('matiere_id')

        # Validation de base
        if not nom or not matiere_id:
            flash("Tous les champs sont obligatoires.")
            return render_template('admin/themes_add.html', matieres=matieres)

        # Vérifier doublon
        existing_theme = themes_col.find_one({
            "nom": nom,
            "matiere_id": ObjectId(matiere_id)
        })
        if existing_theme:
            flash("Ce thème existe déjà pour cette matière.")
            return render_template('admin/themes_add.html', matieres=matieres)

        # Insertion en base
        theme = {
            "nom": nom,
            "matiere_id": ObjectId(matiere_id),
            "lessons": [],
            "created_at": datetime.now()
        }
        themes_col.insert_one(theme)

        flash("Thème ajouté avec succès.")
        return redirect(url_for('admin.list_themes'))

    return render_template('admin/themes_add.html', matieres=matieres)

@admin.route('/themes/edit/<theme_id>', methods=['GET', 'POST'])
@admin_required
def edit_theme(theme_id):
    theme = themes_col.find_one({"_id": ObjectId(theme_id)})
    if not theme:
        flash("Thème introuvable.")
        return redirect(url_for('admin.list_themes'))

    matieres = list(matieres_col.find())

    if request.method == 'POST':
        nom = request.form.get("nom", "").strip()
        matiere_id = request.form.get("matiere_id")

        if not nom or not matiere_id:
            flash("Tous les champs sont obligatoires.")
            return render_template("admin/themes_edit.html", theme=theme, matieres=matieres)

        # Vérifier doublon (autres thèmes)
        duplicate = themes_col.find_one({
            "nom": nom,
            "matiere_id": ObjectId(matiere_id),
            "_id": {"$ne": theme["_id"]}
        })
        if duplicate:
            flash("Un autre thème avec ce nom existe déjà pour cette matière.")
            return render_template("admin/themes_edit.html", theme=theme, matieres=matieres)

        themes_col.update_one(
            {"_id": ObjectId(theme_id)},
            {"$set": {
                "nom": nom,
                "matiere_id": ObjectId(matiere_id),
                "updated_at": datetime.now()
            }}
        )
        flash("Thème mis à jour avec succès.")
        return redirect(url_for("admin.list_themes"))

    return render_template("admin/themes_edit.html", theme=theme, matieres=matieres)

@admin.route('/themes/delete/<theme_id>', methods=['POST'])
@admin_required
def delete_theme(theme_id):
    theme = themes_col.find_one({"_id": ObjectId(theme_id)})
    if not theme:
        flash("Thème introuvable.")
        return redirect(url_for('admin.list_themes'))

    themes_col.delete_one({"_id": ObjectId(theme_id)})
    flash("Thème supprimé avec succès.")
    return redirect(url_for('admin.list_themes'))



# Ajouter une leçon
@admin.route('/lesson/add', methods=['GET', 'POST'])
@admin_required
def add_lesson():
    matieres = list(matieres_col.find())

    if request.method == 'POST':
        matiere_id = request.form.get('matiere_id')
        theme_id = request.form.get('theme_id')
        titre = request.form.get('titre', '').strip()
        contenu = request.form.get('contenu', '').strip()
        fichier = request.files.get('fichier')

        if not matiere_id or not theme_id or not titre:
            flash("Tous les champs obligatoires n'ont pas été remplis.")
            return render_template('admin/lesson_add.html', matieres=matieres)

        if not contenu and (not fichier or fichier.filename == ""):
            flash("Vous devez fournir une description ou un fichier.")
            return render_template('admin/lesson_add.html', matieres=matieres)

        file_path = None
        if fichier and allowed_file(fichier.filename):
            filename = secure_filename(fichier.filename)
            filepath = os.path.join(get_upload_path(), filename)
            fichier.save(filepath)
            file_path = os.path.relpath(filepath, 'static')

        lesson_obj = {
            "titre": titre,
            "contenu": contenu,
            "fichier": file_path,
            "created_at": datetime.now()
        }

        themes_col.update_one(
            {"_id": ObjectId(theme_id)},
            {"$push": {"lessons": lesson_obj}}
        )

        flash("Leçon ajoutée avec succès.")
        return redirect(url_for('admin.add_lesson'))

    return render_template('admin/lesson_add.html', matieres=matieres)

# Modifier une leçon
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

        if fichier and fichier.filename and allowed_file(fichier.filename):
            filename = secure_filename(fichier.filename)
            filepath = os.path.join("static/uploads", filename)
            fichier.save(filepath)
            lesson["fichier"] = filename
        elif fichier and fichier.filename:
            flash("Extension de fichier non autorisée.")
            return render_template("admin/lesson_edit.html", theme=theme, lesson=lesson)

        themes_col.update_one({"_id": ObjectId(theme_id)}, {"$set": {"lessons": lessons}})
        flash("Leçon mise à jour avec succès.")
        return redirect(url_for("admin.list_themes"))

    return render_template("admin/lesson_edit.html", theme=theme, lesson=lessons[index])

# Supprimer une leçon
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
    return redirect(url_for("admin.list_themes"))
