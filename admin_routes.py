import os
from flask import Blueprint, current_app, render_template , flash , url_for, request,jsonify, redirect
from bson import ObjectId
from decorators import role_required
from extensions import mongo
from datetime import datetime
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from bs4 import BeautifulSoup
import bleach
from bleach_config import allowed_tags, allowed_attributes
from collections import defaultdict


admin = Blueprint("admin", __name__, template_folder="templates/admin")


@admin.route("/admin_home")
@role_required("admin")
def admin_home():

    users = list(mongo.db.users.find())  # Accès à la collection "users"
 
    return render_template("home.html", users=users , )

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


@admin.route('/manage_users', methods=['GET', 'POST'])
@role_required("admin")
def manage_users():
    users_col = mongo.db.users  # Assurez-vous que mongo est bien initialisé

    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id')  # peut être None pour add_user

        if action == 'delete' and user_id:
            users_col.delete_one({'_id': ObjectId(user_id)})
            flash("Utilisateur supprimé.", "success")

        elif action == 'toggle_role' and user_id:
            user = users_col.find_one({'_id': ObjectId(user_id)})
            if user:
                current_role = user.get('role', 'eleve')
                new_role = 'professeur' if current_role == 'eleve' else 'eleve'
                users_col.update_one({'_id': ObjectId(user_id)}, {'$set': {'role': new_role}})
                flash(f"Rôle changé en {new_role}.", "success")
            else:
                flash("Utilisateur introuvable.", "error")

        elif action == 'reset_password' and user_id:
            default_password = 'changeme123'
            hashed = generate_password_hash(default_password)
            users_col.update_one({'_id': ObjectId(user_id)}, {'$set': {'password': hashed}})
            flash(f"Mot de passe réinitialisé à : {default_password}", "success")

        elif action == 'add_user':
            name = request.form.get('name', '').strip()
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            role = request.form.get('role', 'eleve')

            if not name or not username or not password:
                flash("Tous les champs sont obligatoires.", "error")
            elif users_col.find_one({'username': username}):
                flash("Nom d'utilisateur déjà utilisé.", "error")
            else:
                hashed_pw = generate_password_hash(password)
                users_col.insert_one({
                    'name': name,
                    'username': username,
                    'password': hashed_pw,
                    'role': role,
                    'created_at': datetime.now()
                })
                flash(f"Utilisateur {name} ajouté.", "success")

        return redirect(url_for('admin.manage_users'))

    # Requête GET : affichage des utilisateurs
    users = list(users_col.find())
    return render_template('admin/manage_users.html', users=users)



# Liste des matières
@admin.route('/matieres')
@role_required("admin")
def list_matieres():
    matieres = list(mongo.db.matieres.find())
    return render_template("admin/matieres_list.html", matieres=matieres)

# Ajouter une matière
@admin.route('/matieres/add', methods=['GET', 'POST'])
@role_required("admin")
def add_matiere():
    if request.method == 'POST':
        nom = request.form.get("nom", "").strip()

        if not nom:
            flash("Le nom de la matière est obligatoire.")
            return render_template("admin/matieres_add.html")

        if mongo.db.matieres.find_one({"nom": nom}):
            flash("Cette matière existe déjà.")
            return render_template("admin/matieres_add.html")

        mongo.db.matieres.insert_one({"nom": nom, "created_at": datetime.now()})
        flash("Matière ajoutée avec succès.")
        return redirect(url_for("admin.list_matieres"))

    return render_template("admin/matieres_add.html")
@admin.route('/admin/api/themes/<matiere_id>')
@role_required("admin")
def api_get_themes_by_matiere(matiere_id):
    try:
        themes = list(mongo.db.themes.find({'matiere_id': ObjectId(matiere_id)}))
        return jsonify([{'_id': str(t['_id']), 'nom': t['nom']} for t in themes])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# Modifier une matière
@admin.route('/matieres/edit/<matiere_id>', methods=['GET', 'POST'])
@role_required("admin")
def edit_matiere(matiere_id):
    matiere = mongo.db.matieres.find_one({"_id": ObjectId(matiere_id)})
    if not matiere:
        flash("Matière introuvable.")
        return redirect(url_for("admin.list_matieres"))

    if request.method == 'POST':
        nom = request.form.get("nom", "").strip()
        description = request.form.get("description", "").strip()

        if not nom:
            flash("Le nom de la matière est obligatoire.")
            return render_template("admin/matieres_edit.html", matiere=matiere)

        if mongo.db.matieres.find_one({"nom": nom, "_id": {"$ne": ObjectId(matiere_id)}}):
            flash("Une autre matière avec ce nom existe déjà.")
            return render_template("admin/matieres_edit.html", matiere=matiere)

        mongo.db.matieres.update_one(
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
@role_required("admin")
def delete_matiere(matiere_id):
    mongo.db.matieres.delete_one({"_id": ObjectId(matiere_id)})
    flash("Matière supprimée.")
    return redirect(url_for("admin.list_matieres"))

# Ajouter un exercice interactif
@admin.route('/exercices', methods=['GET'])
@role_required("admin")
def list_exercices():
    matieres = list(mongo.db.matieres.find())
    matiere_id = request.args.get('matiere_id')
    theme_id = request.args.get('theme_id')

    themes = []
    exercices = []
    current_theme = None

    # Convertir en ObjectId de manière sécurisée
    try:
        matiere_obj_id = ObjectId(matiere_id) if matiere_id else None
    except Exception:
        matiere_obj_id = None

    try:
        theme_obj_id = ObjectId(theme_id) if theme_id else None
    except Exception:
        theme_obj_id = None

    # Charger les thèmes de la matière sélectionnée
    if matiere_obj_id:
        themes = list(mongo.db.themes.find({'matiere_id': matiere_obj_id}))

    # Charger les exercices du thème sélectionné
    if theme_obj_id:
        exercices = list(mongo.db.exercices_interactifs.find({'theme_id': theme_obj_id}))
        current_theme = mongo.db.themes.find_one({'_id': theme_obj_id})

    # Création des mappings pour affichage
    matieres_map = {str(m['_id']): m['nom'] for m in matieres}
    themes_map = {str(t['_id']): t for t in themes}

    # Annoter les exercices avec les noms de thème et matière
    for ex in exercices:
        theme = themes_map.get(str(ex.get('theme_id')))
        if theme:
            ex['theme_nom'] = theme.get('nom', '❓ Thème inconnu')
            ex['matiere_nom'] = matieres_map.get(str(theme.get('matiere_id')), '❓ Matière inconnue')
        else:
            ex['theme_nom'] = '❓ Thème inconnu'
            ex['matiere_nom'] = '❓ Matière inconnue'

    return render_template(
        'admin/exercices_list.html',
        matieres=matieres,
        themes=themes,
        exercices=exercices,
        selected_matiere_id=matiere_id,
        selected_theme_id=theme_id,
        current_theme=current_theme,
    )


@admin.route('/exercice_interactif/add', methods=['GET', 'POST'])
@role_required("admin")
def add_exercice_interactif():
    matieres = list(mongo.db.matieres.find())
    themes = []
    selected_matiere_id = request.args.get('matiere_id')

    if selected_matiere_id:
        try:
            themes = list(mongo.db.themes.find({'matiere_id': ObjectId(selected_matiere_id)}))
        except:
            themes = []

    if request.method == 'POST':
        matiere_id = request.form.get('matiere_id')
        theme_id = request.form.get('theme_id')
        titre = request.form.get('titre', '').strip()
        question = request.form.get('question', '').strip()
        reponse_html = request.form.get('reponse_html', '')

        if not (matiere_id and theme_id and titre and question):
            flash("Tous les champs sont obligatoires.", "danger")
            return render_template('admin/exercice_interactif_add.html', matieres=matieres, themes=themes, selected_matiere_id=selected_matiere_id)

        clean_html = bleach.clean(reponse_html, tags=allowed_tags, attributes=allowed_attributes, strip=True)

        # EXTRAIRE LES RÉPONSES ATTENDUES à partir de la requête POST, en gérant checkbox multiples
        reponses_attendues = {}

        for key in request.form:
            if key in ('matiere_id', 'theme_id', 'titre', 'question', 'reponse_html'):
                continue
            values = request.form.getlist(key)
            if len(values) == 1:
                reponses_attendues[key] = values[0]
            else:
                reponses_attendues[key] = values

        mongo.db.exercices_interactifs.insert_one({
            'matiere_id': ObjectId(matiere_id),
            'theme_id': ObjectId(theme_id),
            'titre': titre,
            'question': question,
            'reponse_html': clean_html,
            'reponses_attendues': reponses_attendues,
            'created_at': datetime.now()
        })

        flash("Exercice interactif ajouté avec succès ✅", "success")
        return redirect(url_for('admin.list_exercices'))

    return render_template(
        'admin.exercice_interactif_add.html',
        matieres=matieres,
        themes=themes,
        selected_matiere_id=selected_matiere_id
    )

@admin.route('/exercice_interactif/edit/<exercice_id>', methods=['GET', 'POST'])
@role_required("admin")
def edit_exercice_interactif(exercice_id):
    exercice = mongo.db.exercices_interactifs.find_one({'_id': ObjectId(exercice_id)})
    if not exercice:
        flash("Exercice introuvable.", "danger")
        return redirect(url_for('admin.list_exercices'))

    matieres = list(mongo.db.matieres.find())
    themes = []
    selected_matiere_id = str(exercice['matiere_id']) if 'matiere_id' in exercice else None

    if selected_matiere_id:
        themes = list(mongo.db.themes.find({'matiere_id': ObjectId(selected_matiere_id)}))

    if request.method == 'POST':
        matiere_id = request.form.get('matiere_id')
        theme_id = request.form.get('theme_id')
        titre = request.form.get('titre', '').strip()
        question = request.form.get('question', '').strip()
        reponse_html = request.form.get('reponse_html', '')

        if not all([matiere_id, theme_id, titre, question]):
            flash("Tous les champs sont obligatoires.", "danger")
            return redirect(request.url)

        clean_html = bleach.clean(reponse_html, tags=allowed_tags, attributes=allowed_attributes, strip=True)

        # Extraction propre des réponses attendues, gérer checkbox multiples
        reponses_attendues = {}

        for key in request.form:
            if key in ('matiere_id', 'theme_id', 'titre', 'question', 'reponse_html'):
                continue
            values = request.form.getlist(key)
            if len(values) == 1:
                reponses_attendues[key] = values[0]
            else:
                reponses_attendues[key] = values

        mongo.db.exercices_interactifs.update_one(
            {'_id': ObjectId(exercice_id)},
            {'$set': {
                'matiere_id': ObjectId(matiere_id),
                'theme_id': ObjectId(theme_id),
                'titre': titre,
                'question': question,
                'reponse_html': clean_html,
                'reponses_attendues': reponses_attendues,
                'updated_at': datetime.now()
            }}
        )

        flash("Exercice mis à jour avec succès ✅", "success")
        return redirect(url_for('admin.list_exercices'))

    return render_template(
        'admin/exercice_interactif_edit.html',
        exercice=exercice,
        matieres=matieres,
        themes=themes,
        selected_matiere_id=selected_matiere_id
    )



@admin.route('/exercice_interactif/delete/<exercice_id>', methods=['GET', 'POST'])
@role_required("admin")
def delete_exercice_interactif(exercice_id):
    exercice = mongo.db.exercices_interactifs.find_one({"_id": ObjectId(exercice_id)})
    
    if not exercice:
        flash("Exercice introuvable.", "danger")
        return redirect(url_for('admin.list_exercices'))

    if request.method == 'POST':
        mongo.db.exercices_interactifs.delete_one({"_id": ObjectId(exercice_id)})
        flash("Exercice supprimé avec succès.", "success")
        return redirect(url_for('admin.list_exercices'))

    # Récupérer les infos associées
    theme = mongo.db.themes.find_one({"_id": exercice.get("theme_id")})
    matiere = None
    if theme:
        matiere = mongo.db.matieres.find_one({"_id": theme.get("matiere_id")})

    return render_template(
        'admin/exercice_interactif_delete.html',
        exercice=exercice,
        theme=theme,
        matiere=matiere
    )







# Liste des thèmes
@admin.route('/themes')
@role_required("admin")
def list_themes():
    themes = list(mongo.db.themes.find())
    matieres_dict = {m["_id"]: m["nom"] for m in mongo.db.matieres.find()}
    for theme in themes:
        theme["matiere_nom"] = matieres_dict.get(theme["matiere_id"], "Inconnue")
    return render_template("admin/themes_list.html", themes=themes)

@admin.route('/themes/add', methods=['GET', 'POST'])
@role_required("admin")
def add_theme():
    matieres = list(mongo.db.matieres.find())

    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        matiere_id = request.form.get('matiere_id')

        # Validation de base
        if not nom or not matiere_id:
            flash("Tous les champs sont obligatoires.")
            return render_template('admin/themes_add.html', matieres=matieres)

        # Vérifier doublon
        existing_theme = mongo.db.themes.find_one({
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
        mongo.db.themes.insert_one(theme)

        flash("Thème ajouté avec succès.")
        return redirect(url_for('admin.list_themes'))

    return render_template('admin/themes_add.html', matieres=matieres)

@admin.route('/themes/edit/<theme_id>', methods=['GET', 'POST'])
@role_required("admin")
def edit_theme(theme_id):
    theme = mongo.db.themes.find_one({"_id": ObjectId(theme_id)})
    if not theme:
        flash("Thème introuvable.")
        return redirect(url_for('admin.list_themes'))

    matieres = list(mongo.db.matieres.find())

    if request.method == 'POST':
        nom = request.form.get("nom", "").strip()
        matiere_id = request.form.get("matiere_id")

        if not nom or not matiere_id:
            flash("Tous les champs sont obligatoires.")
            return render_template("admin/themes_edit.html", theme=theme, matieres=matieres)

        # Vérifier doublon (autres thèmes)
        duplicate = mongo.db.themes.find_one({
            "nom": nom,
            "matiere_id": ObjectId(matiere_id),
            "_id": {"$ne": theme["_id"]}
        })
        if duplicate:
            flash("Un autre thème avec ce nom existe déjà pour cette matière.")
            return render_template("admin/themes_edit.html", theme=theme, matieres=matieres)

        mongo.db.themes.update_one(
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
@role_required("admin")
def delete_theme(theme_id):
    theme = mongo.db.themes.find_one({"_id": ObjectId(theme_id)})
    if not theme:
        flash("Thème introuvable.")
        return redirect(url_for('admin.list_themes'))

    mongo.db.themes.delete_one({"_id": ObjectId(theme_id)})
    flash("Thème supprimé avec succès.")
    return redirect(url_for('admin.list_themes'))



# Ajouter une leçon
from bson.errors import InvalidId

@admin.route('/lesson/add', methods=['GET', 'POST'])
@role_required("admin")
def add_lesson():
    matieres = list(mongo.db.matieres.find())
    selected_matiere_id = request.form.get('matiere_id') or request.args.get('matiere_id')
    selected_theme_id = request.form.get('theme_id')
    themes = []

    if selected_matiere_id:
        try:
            matiere_oid = ObjectId(selected_matiere_id)
            themes = list(mongo.db.themes.find({'matiere_id': matiere_oid}))
        except (InvalidId, TypeError):
            flash("ID de matière invalide.")
            themes = []

    if request.method == 'POST':
        titre = request.form.get('titre', '').strip()
        contenu = request.form.get('contenu', '').strip()
        fichier = request.files.get('fichier')

        if not selected_matiere_id or not selected_theme_id or not titre:
            flash("Tous les champs obligatoires n'ont pas été remplis.")
            return render_template(
                'admin/lesson_add.html',
                matieres=matieres,
                themes=themes,
                selected_matiere_id=selected_matiere_id,
                selected_theme_id=selected_theme_id
            )

        if not contenu and (not fichier or fichier.filename == ""):
            flash("Vous devez fournir une description ou un fichier.")
            return render_template(
                'admin/lesson_add.html',
                matieres=matieres,
                themes=themes,
                selected_matiere_id=selected_matiere_id,
                selected_theme_id=selected_theme_id
            )

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

        try:
            mongo.db.themes.update_one(
                {"_id": ObjectId(selected_theme_id)},
                {"$push": {"lessons": lesson_obj}}
            )
            flash("Leçon ajoutée avec succès.")
            return redirect(url_for('admin.add_lesson', matiere_id=selected_matiere_id))
        except InvalidId:
            flash("Thème invalide.")

    return render_template(
        'admin/lesson_add.html',
        matieres=matieres,
        themes=themes,
        selected_matiere_id=selected_matiere_id,
        selected_theme_id=selected_theme_id
    )


# Modifier une leçon
@admin.route('/lecon/edit/<theme_id>/<int:index>', methods=["GET", "POST"])
@role_required("admin")
def edit_lecon(theme_id, index):
    theme = mongo.db.themes.find_one({"_id": ObjectId(theme_id)})
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

        mongo.db.themes.update_one({"_id": ObjectId(theme_id)}, {"$set": {"lessons": lessons}})
        flash("Leçon mise à jour avec succès.")
        return redirect(url_for("admin.list_themes"))

    return render_template("admin/lesson_edit.html", theme=theme, lesson=lessons[index])

# Supprimer une leçon
@admin.route('/lecon/delete/<theme_id>/<int:index>', methods=["POST"])
@role_required("admin")
def delete_lecon(theme_id, index):
    theme = mongo.db.themes.find_one({"_id": ObjectId(theme_id)})
    if not theme:
        flash("Thème introuvable.")
        return redirect(url_for("admin.list_themes"))

    lessons = theme.get("lessons", [])
    if index < 0 or index >= len(lessons):
        flash("Leçon introuvable.")
        return redirect(url_for("admin.list_themes"))

    del lessons[index]
    mongo.db.themes.update_one({"_id": ObjectId(theme_id)}, {"$set": {"lessons": lessons}})

    flash("Leçon supprimée avec succès.")
    return redirect(url_for("admin.list_themes"))


@admin.route('/professeurs')
@role_required("admin")
def list_professeurs():
    professeurs = list(mongo.db.users.find({"role": "professeur"}))
    return render_template("admin/professeurs_list.html", professeurs=professeurs)


@admin.route('/professeurs/add', methods=['GET', 'POST'])
@role_required("admin")
def add_professeur():
    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not nom or not email or not password:
            flash("Tous les champs sont obligatoires.")
            return render_template('admin/professeurs_add.html')

        if mongo.db.users.find_one({"email": email}):
            flash("Un utilisateur avec cet e-mail existe déjà.")
            return render_template('admin/professeurs_add.html')

        # Mot de passe en clair (à sécuriser avec hash plus tard si non déjà fait ailleurs)
        user = {
            "nom": nom,
            "email": email,
            "password": password,
            "role": "professeur",
            "created_at": datetime.now()
        }
        mongo.db.users.insert_one(user)
        flash("Professeur ajouté avec succès.")
        return redirect(url_for('admin.list_professeurs'))

    return render_template('admin/professeurs_add.html')

@admin.route('/professeurs/edit/<user_id>', methods=['GET', 'POST'])
@role_required("admin")
def edit_professeur(user_id):
    professeur = mongo.db.users.find_one({"_id": ObjectId(user_id), "role": "professeur"})
    if not professeur:
        flash("Professeur introuvable.")
        return redirect(url_for('admin.list_professeurs'))

    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        email = request.form.get('email', '').strip()

        if not nom or not email:
            flash("Tous les champs sont obligatoires.")
            return render_template('admin/professeurs_edit.html', professeur=professeur)

        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"nom": nom, "email": email, "updated_at": datetime.now()}}
        )
        flash("Professeur mis à jour.")
        return redirect(url_for('admin.list_professeurs'))

    return render_template('admin/professeurs_edit.html', professeur=professeur)

@admin.route('/professeurs/delete/<user_id>', methods=['POST'])
@role_required("admin")
def delete_professeur(user_id):
    result = mongo.db.users.delete_one({"_id": ObjectId(user_id), "role": "professeur"})
    if result.deleted_count == 0:
        flash("Suppression impossible : professeur introuvable.")
    else:
        flash("Professeur supprimé avec succès.")
    return redirect(url_for('admin.list_professeurs'))
